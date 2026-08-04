"""App configuration overrides for third-party packages."""

from django.apps import AppConfig


class PayPalIpnConfig(AppConfig):
    """Pin django-paypal's primary key type to what its migrations already use.

    The project sets DEFAULT_AUTO_FIELD to BigAutoField, which would otherwise
    apply to django-paypal's models too and make Django want to generate a new
    migration inside site-packages. The IPN table is untouched.
    """

    name = "paypal.standard.ipn"
    label = "ipn"
    default_auto_field = "django.db.models.AutoField"
