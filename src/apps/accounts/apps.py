from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.accounts"

    def ready(self):
        # force import OpenAPI extensions
        import apps.accounts.api.v1.openapi  # noqa: F401
