import base64

from django.conf import settings
from django.core.signing import BadSignature, TimestampSigner


class URLSafeTokenSigner:
    """Generate timestampsigner wit url safe ."""

    def __init__(self, salt):
        self.signer = TimestampSigner(salt=salt)

    def sign(self, value):
        """Sign token and make it base64 format."""
        signed = self.signer.sign(value)
        # encode base64
        encoded = base64.urlsafe_b64encode(signed.encode()).decode()
        return encoded.rstrip("=")  # remove padding

    def unsign(self, token, max_age=None):
        """Unsign token and decode base64."""
        padding = (4 - len(token) % 4) % 4
        token += "=" * padding

        try:
            decoded = base64.urlsafe_b64decode(token).decode()
        except Exception as e:
            raise BadSignature(f"Invalid base64: {e}") from e
        return self.signer.unsign(decoded, max_age=max_age)


email_verification_signer = URLSafeTokenSigner(
    salt="email_verification"
)  # add salt to avoid using it in different places like reset password
VERIFICATION_EXPIRY_HOURS = settings.VERIFICATION_EXPIRY_HOURS
