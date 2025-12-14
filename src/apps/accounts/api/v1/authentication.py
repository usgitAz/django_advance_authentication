from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.authentication import JWTAuthentication

from apps.accounts.models.jwt_token_blacklist import TokenBlacklist


class JWTAuthenticationWithBlacklist(JWTAuthentication):
    """JWT Authentication that checks if the token's jti is in the blacklist.

    Extends the default JWTAuthentication to validate tokens against
    the TokenBlacklist model. If a token's jti is found in the blacklist,
    authentication fails.
    """

    def authenticate(self, request):
        """Authenticate the request using JWT and check blacklist.

        Returns:
            tuple: (user, token) if authentication succeeds
            None: if no authentication is provided

        Raises:
            AuthenticationFailed: if token is invalid or blacklisted

        """
        # Call parent authenticate to get user and token
        result = super().authenticate(request)

        if result is None:
            return None

        user, token = result

        # Check if the token's jti is blacklisted
        jti = token.get("jti")

        if jti and TokenBlacklist.is_blacklisted(jti):
            raise AuthenticationFailed("Token has been revoked/blacklisted")

        return user, token
