from drf_spectacular.extensions import OpenApiAuthenticationExtension


class JWTBlacklistAuthenticationScheme(OpenApiAuthenticationExtension):
    """Open Api extenshion for showing authroize section in docs."""

    target_class = "apps.accounts.api.v1.authentication.JWTAuthenticationWithBlacklist"
    name = "BearerAuth"

    def get_security_definition(self, auto_schema):
        return {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }
