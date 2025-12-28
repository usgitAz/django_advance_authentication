import structlog
from django.conf import settings
from django.core.mail import send_mail
from django.core.signing import BadSignature, SignatureExpired

from apps.accounts.models import User

from .tokens import VERIFICATION_EXPIRY_HOURS, email_verification_signer

logger = structlog.get_logger(__name__)


def send_verification_email(user):
    token = email_verification_signer.sign(f"{user.pk}:{user.email}")
    verify_url = f"{settings.SITE_URL}/api/v1/users/verify-email/{token}"

    subject = "Verify Your Email Address"
    message = (
        f"Hi {user.first_name}\n"
        f"verify your email with below link :\n"
        f"verify link : {verify_url}\n"
        f"this link is valid for {VERIFICATION_EXPIRY_HOURS} hour."
    )
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
        logger.info(
            "verification email sent",
            user_id=user.pk,
            user_email=user.email,
        )
    except Exception as e:
        logger.exception(
            "failed to send verification email",
            user_id=user.pk,
            user_email=user.email,
            error_type=type(e).__name__,
        )
        raise


def verify_email_token(token):
    """Verify email token and return corresponding user.

    Args:
        token: Base64-encoded signed token containing user_id:email

    Returns:
        User: User instance if token is valid and not expired
        None: If token is invalid or expired

    Raises:
        ValueError: If token format is invalid or user not found

    """
    try:
        value = email_verification_signer.unsign(
            token,
            max_age=VERIFICATION_EXPIRY_HOURS * 3600,
        )

        # Validate format
        if ":" not in value:
            raise ValueError("Invalid token structure")

        user_id, email = value.split(":", 1)

        # Get user
        user = User.objects.get(pk=user_id, email=email)

        logger.debug(
            "token verified successfully",
            user_id=user.pk,
            user_email=user.email,
        )

        return user

    except (BadSignature, SignatureExpired) as e:
        logger.warning(
            "token validation failed",
            error_type=type(e).__name__,
            token_preview=token[:20] if len(token) > 20 else token,
        )
        return None

    except (ValueError, User.DoesNotExist) as e:
        logger.error(
            "invalid token data",
            error=str(e),
            token_preview=token[:20] if len(token) > 20 else token,
        )
        raise ValueError(f"Invalid token: {e}") from e
