"""URL configuration for the Fully Alive Retreat site."""

from django.conf import settings
from django.contrib import admin
from django.core.exceptions import ImproperlyConfigured
from django.urls import include, path
from django.views.generic import RedirectView

from registration import views

handler404 = "registration.views.not_found"
handler500 = "registration.views.error"

urlpatterns = [
    # Public pages
    path("", views.home, name="home"),
    path("home/", views.home, name="home_alias"),
    path("info/", views.info, name="info"),
    path("schedule/", views.schedule, name="schedule"),
    path("fellowship/", views.fellowship, name="fellowship"),
    path("photos/", views.photos, name="photos"),
    path("paypal-issues/", views.paypal_issues, name="paypal_issues"),
    path("robots.txt", views.robots_txt, name="robots"),
    # Registration + payment
    path("registration/", views.register, name="register"),
    path("pay/<int:camper_id>/", views.pay_now, name="pay_now"),
    path("return/", views.return_url, name="your-return-view"),
    path("cancel/", views.canceled_url, name="your-cancel-view"),
    path("full/", views.full, name="full"),
    # Staff
    path("login/", views.CamperLoginView.as_view(), name="login"),
    path("logout/", views.camper_logout, name="logout"),
    path("camper-info/", views.camper_info, name="camper_info"),
    path("camper-info/<slug:season>/", views.camper_info, name="camper_info_season"),
    path("camper-info/<slug:season>/export.csv", views.camper_export, name="camper_export"),
    path("registration-status/", views.set_registration_status, name="set_registration_status"),
    path("reconcile-payments/", views.reconcile_payments, name="reconcile_payments"),
    # Admin
    path(f"{settings.ADMIN_URL}/", admin.site.urls),
]

# The PayPal IPN listener path is configured out of band so it can be rotated
# without a code change. Refusing to boot is safer than silently mounting the
# listener at a predictable path.
if not settings.PAYPAL_ENDPOINT:
    raise ImproperlyConfigured(
        "PAYPAL_ENDPOINT is not set. Set it to the secret path PayPal should "
        "post IPN notifications to. See .env.example."
    )

urlpatterns.append(
    path(f"{settings.PAYPAL_ENDPOINT.strip('/')}/", include("paypal.standard.ipn.urls"))
)

# Legacy URLs kept as permanent redirects so existing links, bookmarks and the
# PayPal account's stored return URLs keep working after the rebuild.
_LEGACY_REDIRECTS = {
    "register": "registration/",
    "camper_info": "camper-info/",
    "paypal_issues": "paypal-issues/",
    "check_who_paid": "camper-info/",
    "accounts/login": "login/",
    "camper_info/2026_winter_camper_info": "camper-info/winter-2026/",
    "camper_info/2025_summer_camper_info": "camper-info/summer-2025/",
    "camper_info/2024_summer_camper_info": "camper-info/summer-2024/",
    "camper_info/2023_summer_camper_info": "camper-info/summer-2023/",
    "camper_info/2022_summer_camper_info": "camper-info/summer-2022/",
    "camper_info/2021_fall_camper_info": "camper-info/fall-2021/",
    "camper_info/2020_camper_info_fall": "camper-info/fall-2020/",
    "camper_info/2020_spring_camper_info": "camper-info/spring-2020/",
    "camper_info/2019_camper_info_spring": "camper-info/spring-2019/",
}

urlpatterns += [
    path(f"{old}/", RedirectView.as_view(url=f"/{new}", permanent=True))
    for old, new in _LEGACY_REDIRECTS.items()
]
