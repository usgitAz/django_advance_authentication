"""Tests for email verification functionality."""

from unittest.mock import patch

import pytest
from django.core import mail
from django.core.signing import SignatureExpired
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.models import User
from core.email import send_verification_email, verify_email_token
from core.tokens import email_verification_signer


@pytest.mark.django_db
class TestSendVerificationEmail:
    """Test send_verification_email function."""

    def test_sends_email_with_correct_data(self, user_factory):
        """Email is sent with proper subject, recipient, and token."""
        user = user_factory(first_name="John", email="john@example.com")

        send_verification_email(user)

        assert len(mail.outbox) == 1
        email = mail.outbox[0]
        assert email.subject == "Verify Your Email Address"
        assert email.to == ["john@example.com"]
        assert "John" in email.body
        assert "/api/v1/users/verify-email/" in email.body

    def test_token_contains_user_data(self, user_factory):
        """Generated token contains user ID and email."""
        user = user_factory()

        send_verification_email(user)

        email_body = mail.outbox[0].body
        # Extract token from email body
        token_start = email_body.find("/verify-email/") + len("/verify-email/")
        token_end = email_body.find("\n", token_start)
        token = email_body[token_start:token_end].strip()

        # Verify token contains correct data
        value = email_verification_signer.unsign(token)
        user_id, email = value.split(":")
        assert str(user.pk) == user_id
        assert user.email == email

    def test_handles_user_without_first_name(self, user_factory):
        """Email is sent even if user has no first name."""
        user = user_factory(first_name="")

        send_verification_email(user)

        assert len(mail.outbox) == 1
        assert "Hi there" in mail.outbox[0].body or "Hi " in mail.outbox[0].body

    @patch("core.email.send_mail")
    def test_raises_exception_on_smtp_error(self, mock_send_mail, user_factory):
        """Exception is raised when email sending fails."""
        user = user_factory()
        mock_send_mail.side_effect = Exception("SMTP Error")

        with pytest.raises(Exception, match="SMTP Error"):
            send_verification_email(user)

    @patch("core.email.logger")
    def test_logs_success(self, mock_logger, user_factory):
        """Success is logged when email is sent."""
        user = user_factory()

        send_verification_email(user)

        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args
        assert "verification email sent" in call_args[0][0]

    @patch("core.email.send_mail")
    @patch("core.email.logger")
    def test_logs_failure(self, mock_logger, mock_send_mail, user_factory):
        """Failure is logged when email sending fails."""
        user = user_factory()
        mock_send_mail.side_effect = RuntimeError("SMTP Error")

        with pytest.raises(RuntimeError):
            send_verification_email(user)

        mock_logger.exception.assert_called_once()


@pytest.mark.django_db
class TestVerifyEmailToken:
    """Test verify_email_token function."""

    def test_returns_user_for_valid_token(self, user_factory):
        """Valid token returns correct user."""
        user = user_factory()
        token = email_verification_signer.sign(f"{user.pk}:{user.email}")

        result = verify_email_token(token)

        assert result == user

    def test_returns_none_for_expired_token(self, user_factory):
        """Expired token returns None."""
        user = user_factory()
        token = email_verification_signer.sign(f"{user.pk}:{user.email}")

        with patch("core.email.email_verification_signer.unsign") as mock_unsign:
            mock_unsign.side_effect = SignatureExpired("Expired")
            result = verify_email_token(token)

        assert result is None

    def test_returns_none_for_invalid_signature(self, user_factory):
        """Invalid signature returns None."""
        result = verify_email_token("invalid_to:ken_xyz")

        assert result is None

    def test_raises_for_malformed_token(self, user_factory):
        """Malformed token raises ValueError."""
        user = user_factory()
        # Token without colon separator
        token = email_verification_signer.sign(f"{user.pk}")

        with pytest.raises(ValueError, match="Invalid token"):
            verify_email_token(token)

    def test_raises_for_nonexistent_user(self, user_factory):
        """Token for non-existent user raises ValueError."""
        token = email_verification_signer.sign(
            "08e19442-a783-45e8-afeb-a720f0380ede:fake@example.com"
        )

        with pytest.raises(ValueError, match="Invalid token"):
            verify_email_token(token)

    def test_validates_email_matches(self, user_factory):
        """User is only returned if email in token matches."""
        user = user_factory(email="correct@example.com")
        # Token with wrong email
        token = email_verification_signer.sign(f"{user.pk}:wrong@example.com")

        with pytest.raises(ValueError):
            verify_email_token(token)

    @patch("core.email.logger")
    def test_logs_success(self, mock_logger, user_factory):
        """Successful verification is logged."""
        user = user_factory()
        token = email_verification_signer.sign(f"{user.pk}:{user.email}")

        verify_email_token(token)

        mock_logger.debug.assert_called_once()

    @patch("core.email.logger")
    def test_logs_expiry(self, mock_logger, user_factory):
        """Expired token is logged as warning."""
        user = user_factory()
        token = email_verification_signer.sign(f"{user.pk}:{user.email}")

        with patch("core.email.email_verification_signer.unsign") as mock_unsign:
            mock_unsign.side_effect = SignatureExpired("Expired")
            verify_email_token(token)

        mock_logger.warning.assert_called_once()

    @patch("core.email.logger")
    def test_logs_invalid_data(self, mock_logger):
        """Invalid token data is logged as error."""
        token = email_verification_signer.sign("invalid_format")

        with pytest.raises(ValueError):
            verify_email_token(token)

        mock_logger.error.assert_called_once()


@pytest.mark.django_db
class TestVerifyEmailEndpoint:
    """Test /api/v1/users/verify-email/{token}/ endpoint."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.client = APIClient()

    def test_verifies_email_with_valid_token(self, user_factory):
        """Valid token verifies user email."""
        user = user_factory(email_verified=False)
        token = email_verification_signer.sign(f"{user.pk}:{user.email}")

        response = self.client.get(f"/api/v1/users/verify-email/{token}/")

        assert response.status_code == status.HTTP_200_OK
        assert "successfully verified" in response.data["detail"].lower()

        user.refresh_from_db()
        assert user.email_verified is True

    def test_returns_error_for_expired_token(self, user_factory):
        """Expired token returns 400 error."""
        user = user_factory(email_verified=False)
        token = email_verification_signer.sign(f"{user.pk}:{user.email}")

        with patch("core.email.email_verification_signer.unsign") as mock_unsign:
            mock_unsign.side_effect = SignatureExpired("Expired")
            response = self.client.get(f"/api/v1/users/verify-email/{token}/")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "expired" in response.data["detail"].lower()

    def test_returns_error_for_invalid_token(self):
        """Invalid token returns 400 error."""
        response = self.client.get("/api/v1/users/verify-email/invalid_token/")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "invalid" in response.data["detail"].lower()

    def test_handles_already_verified_email(self, user_factory):
        """Already verified email returns 200 with message."""
        user = user_factory(email_verified=True)
        token = email_verification_signer.sign(f"{user.pk}:{user.email}")

        response = self.client.get(f"/api/v1/users/verify-email/{token}/")

        assert response.status_code == status.HTTP_200_OK
        assert "already verified" in response.data["detail"].lower()

    def test_does_not_update_already_verified(self, user_factory):
        """Already verified users are not re-saved."""
        user = user_factory(email_verified=True)
        token = email_verification_signer.sign(f"{user.pk}:{user.email}")
        original_date = user.date_joined

        self.client.get(f"/api/v1/users/verify-email/{token}/")

        user.refresh_from_db()
        assert user.date_joined == original_date

    def test_returns_error_for_malformed_token(self, user_factory):
        """Malformed token returns 400 error."""
        user = user_factory()
        token = email_verification_signer.sign(f"{user.pk}")  # Missing email

        response = self.client.get(f"/api/v1/users/verify-email/{token}/")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "format" in response.data["detail"].lower()

    def test_allows_unauthenticated_access(self, user_factory):
        """Endpoint is accessible without authentication."""
        user = user_factory(email_verified=False)
        token = email_verification_signer.sign(f"{user.pk}:{user.email}")

        # No authentication
        response = self.client.get(f"/api/v1/users/verify-email/{token}/")

        assert response.status_code == status.HTTP_200_OK

    @patch("apps.accounts.api.v1.viewsets.logger")
    def test_logs_verification_attempt(self, mock_logger, user_factory):
        """Verification attempts are logged."""
        user = user_factory(email_verified=False)
        token = email_verification_signer.sign(f"{user.pk}:{user.email}")

        self.client.get(f"/api/v1/users/verify-email/{token}/")

        # Check that info log was called
        info_calls = list(mock_logger.info.call_args_list)
        assert len(info_calls) >= 1

    @patch("apps.accounts.api.v1.viewsets.logger")
    def test_logs_verification_success(self, mock_logger, user_factory):
        """Successful verification is logged."""
        user = user_factory(email_verified=False)
        token = email_verification_signer.sign(f"{user.pk}:{user.email}")

        self.client.get(f"/api/v1/users/verify-email/{token}/")

        # Find the success log call
        success_logged = any(
            "verified successfully" in str(call)
            for call in mock_logger.info.call_args_list
        )
        assert success_logged

    @patch("apps.accounts.api.v1.viewsets.logger")
    def test_logs_already_verified(self, mock_logger, user_factory):
        """Already verified is logged."""
        user = user_factory(email_verified=True)
        token = email_verification_signer.sign(f"{user.pk}:{user.email}")

        self.client.get(f"/api/v1/users/verify-email/{token}/")

        mock_logger.info.assert_called()

    def test_url_safe_token_works(self, user_factory):
        """URL-safe base64 tokens work correctly."""
        user = user_factory()
        token = email_verification_signer.sign(f"{user.pk}:{user.email}")

        # Token should not need URL encoding
        assert ":" not in token
        assert "@" not in token
        assert "/" not in token or token.count("/") == 1  # Only trailing slash

        response = self.client.get(f"/api/v1/users/verify-email/{token}/")
        assert response.status_code == status.HTTP_200_OK

    @patch("apps.accounts.api.v1.viewsets.verify_email_token")
    def test_handles_unexpected_exception(self, mock_verify):
        """Unexpected exceptions return 500 error."""
        mock_verify.side_effect = RuntimeError("Unexpected error")

        response = self.client.get("/api/v1/users/verify-email/sometoken/")

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "error occurred" in response.data["detail"].lower()

    @patch("apps.accounts.api.v1.viewsets.verify_email_token")
    @patch("apps.accounts.api.v1.viewsets.logger")
    def test_logs_unexpected_exception(self, mock_logger, mock_verify):
        """Unexpected exceptions are logged."""
        mock_verify.side_effect = RuntimeError("Unexpected error")

        self.client.get("/api/v1/users/verify-email/sometoken/")

        mock_logger.exception.assert_called_once()
        call_args = mock_logger.exception.call_args
        assert "unexpected error" in call_args[0][0]


@pytest.mark.django_db
class TestUserRegistrationWithVerification:
    """Test user registration sends verification email."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.client = APIClient()
        self.register_url = "/api/v1/users/"

    def test_registration_sends_verification_email(self):
        """Registration sends verification email."""
        data = {
            "email": "newuser@example.com",
            "password": "testpass123",
            "retype_password": "testpass123",
            "first_name": "Test",
            "last_name": "User",
        }

        response = self.client.post(self.register_url, data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert len(mail.outbox) == 1
        assert mail.outbox[0].to == ["newuser@example.com"]

    def test_user_created_with_unverified_email(self):
        """New users have email_verified=False."""
        data = {
            "email": "newuser@example.com",
            "password": "testpass123",
            "retype_password": "testpass123",
            "first_name": "Test",
            "last_name": "User",
        }

        self.client.post(self.register_url, data, format="json")

        user = User.objects.get(email="newuser@example.com")
        assert user.email_verified is False

    @patch("core.email.send_mail")
    def test_user_created_even_if_email_fails(self, mock_send_mail):
        """User is created even if verification email fails."""
        mock_send_mail.side_effect = Exception("SMTP Error")

        data = {
            "email": "newuser@example.com",
            "password": "testpass123",
            "retype_password": "testpass123",
            "first_name": "Test",
            "last_name": "User",
        }

        response = self.client.post(self.register_url, data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert User.objects.filter(email="newuser@example.com").exists()

    def test_verification_token_in_email_is_valid(self):
        """Token in verification email can verify the user."""
        data = {
            "email": "newuser@example.com",
            "password": "testpass123",
            "retype_password": "testpass123",
            "first_name": "Test",
            "last_name": "User",
        }

        self.client.post(self.register_url, data, format="json")

        # Extract token from email
        email_body = mail.outbox[0].body
        token_start = email_body.find("/verify-email/") + len("/verify-email/")
        token_end = email_body.find("\n", token_start)
        token = email_body[token_start:token_end].strip()

        # Verify using the token
        response = self.client.get(f"/api/v1/users/verify-email/{token}/")
        assert response.status_code == status.HTTP_200_OK

        user = User.objects.get(email="newuser@example.com")
        assert user.email_verified is True
