from django.apps import AppConfig


class RegistrationConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "registration"
    verbose_name = "Camp registration"

    def ready(self):
        # Connects the PayPal IPN verification handlers.
        from registration import signals  # noqa: F401
