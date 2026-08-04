"""Views for the Fully Alive Retreat site.

Public pages are thin renders. Registration delegates all validation to
``CamperRegistrationForm``. Nothing here decides whether a camper has paid —
that lives in ``registration.signals``, driven by PayPal's IPN callback.
"""

import csv
import datetime
import json
import logging
from http import HTTPStatus

from django.conf import settings
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.templatetags.static import static
from django.urls import reverse
from django.views.decorators.http import require_POST
from paypal.standard.forms import PayPalPaymentsForm

from registration.churches import CHURCH_CHOICES
from registration.forms import CamperRegistrationForm
from registration.models import Camper, CampSeason

logger = logging.getLogger("registration")

# Columns shown in the staff camper table and the CSV export.
CAMPER_COLUMNS = [
    ("id", "ID"),
    ("first_name", "First name"),
    ("last_name", "Last name"),
    ("date_of_birth", "Date of birth"),
    ("gender", "Gender"),
    ("email", "Email"),
    ("phone", "Phone"),
    ("city", "City"),
    ("state", "State"),
    ("church", "Church"),
    ("pastor", "Pastor"),
    ("pastor_number", "Pastor phone"),
    ("church_member", "Church member"),
    ("not_married", "Never married"),
    ("med_notes", "Medical notes"),
    ("tshirt_size", "Sage hoodie"),
    ("swshirt_size", "Forest hoodie"),
    ("mug", "Mug"),
    ("status", "Status"),
    ("amount_due", "Amount due"),
    ("amount_paid", "Amount paid"),
    ("paid", "Paid"),
    ("payment_flagged", "Flagged"),
    ("email_sent", "Email sent"),
    ("created", "Registered"),
]


# ---------------------------------------------------------------------------
# Public pages
# ---------------------------------------------------------------------------

def home(request):
    season = CampSeason.active()
    context = {"nav": "home"}

    if season and season.starts_at and season.ends_at:
        # The individual day numbers shown as chips on the hero band.
        start, end = season.starts_at.date(), season.ends_at.date()
        context["season_days"] = [
            (start + datetime.timedelta(days=offset)).day
            for offset in range((end - start).days + 1)
        ]
        context["event_schema"] = _event_schema(request, season)

    return render(request, "home.html", context)


def _event_schema(request, season):
    """JSON-LD describing the retreat, for search results and link previews."""
    schema = {
        "@context": "https://schema.org",
        "@type": "Event",
        "name": season.name,
        "startDate": season.starts_at.isoformat(),
        "eventAttendanceMode": "https://schema.org/OfflineEventAttendanceMode",
        "eventStatus": "https://schema.org/EventScheduled",
        "description": settings.SITE_TAGLINE,
        "organizer": {"@type": "Organization", "name": "NWASBC Union"},
        "url": request.build_absolute_uri("/"),
        "image": request.build_absolute_uri(static("registration/img/og-cover.jpg")),
    }
    if season.ends_at:
        schema["endDate"] = season.ends_at.isoformat()
    if season.venue_name:
        schema["location"] = {
            "@type": "Place",
            "name": season.venue_name,
            "address": season.venue_address,
        }
    if season.base_price is not None:
        schema["offers"] = {
            "@type": "Offer",
            "price": str(season.base_price),
            "priceCurrency": settings.PAYPAL_CURRENCY,
            "url": request.build_absolute_uri(reverse("register")),
            "availability": (
                "https://schema.org/InStock"
                if season.accepting_registrations
                else "https://schema.org/SoldOut"
            ),
        }
    # "</" is escaped so the payload can never terminate the surrounding
    # <script> element early.
    return json.dumps(schema, ensure_ascii=False).replace("</", "<\\/")


def info(request):
    return render(request, "info.html", {"nav": "info"})


def schedule(request):
    return render(request, "schedule.html", {"nav": "schedule"})


def fellowship(request):
    return render(request, "fellowship.html", {"nav": "fellowship"})


def photos(request):
    return render(request, "photos.html", {"nav": "photos"})


def paypal_issues(request):
    return render(request, "paypal_issues.html")


def full(request):
    return render(request, "full.html", status=HTTPStatus.OK)


def error(request):
    return render(request, "error.html", status=HTTPStatus.INTERNAL_SERVER_ERROR)


def not_found(request, exception=None):
    return render(request, "not_found.html", status=HTTPStatus.NOT_FOUND)


def robots_txt(request):
    lines = [
        "User-agent: *",
        # The staff pages render camper PII including medical notes.
        "Disallow: /camper-info/",
        "Disallow: /pay/",
        f"Disallow: /{settings.ADMIN_URL}/",
        "",
        f"Sitemap: https://{settings.DOMAIN}/",
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain")


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

def register(request):
    """Show and process the registration form.

    Previously this was split across two views at two URLs (``/registration``
    rendered the form, ``/register`` processed it), which meant a POST could
    reach the handler without passing the checks the renderer applied.
    """
    season = CampSeason.active()

    if season is None:
        return render(request, "hasnt_opened.html", status=HTTPStatus.OK)
    if not season.registration_open:
        return render(request, "closed.html", status=HTTPStatus.OK)
    if season.is_full:
        return render(request, "full.html", status=HTTPStatus.OK)

    if request.method == "POST":
        form = CamperRegistrationForm(request.POST, season=season)
        if form.is_valid():
            camper = form.save()
            logger.info("Camper %s registered for %s.", camper.pk, season.slug)

            # Ineligible registrations are still recorded so the team can see
            # who applied, but they do not continue to payment.
            if camper.status == Camper.Status.REJECTED_MARRIED:
                return render(request, "married_error.html", status=HTTPStatus.OK)
            if camper.status == Camper.Status.REJECTED_AGE:
                return render(request, "age_error.html", status=HTTPStatus.OK)

            return redirect("pay_now", camper_id=camper.pk)
    else:
        form = CamperRegistrationForm(season=season)

    taken = season.paid_count
    return render(
        request,
        "register.html",
        {
            "form": form,
            "season": season,
            "churches": CHURCH_CHOICES,
            "capacity_percent": min(round(taken / season.capacity * 100), 100) if season.capacity else 0,
            "nav": "register",
        },
        status=HTTPStatus.BAD_REQUEST if request.method == "POST" else HTTPStatus.OK,
    )


def pay_now(request, camper_id):
    """Render the PayPal button for a registration.

    The amount comes from ``Camper.amount_due``, which was computed on the
    server. PayPal reports back what was actually paid, and the IPN handler
    compares the two before marking anyone paid — so a tampered amount here
    cannot produce a paid registration.
    """
    camper = get_object_or_404(Camper, pk=camper_id)
    season = camper.season

    if camper.paid:
        return render(request, "success.html")

    paypal_dict = {
        "business": settings.PAYPAL_RECEIVER_EMAIL,
        "amount": f"{camper.amount_due:.2f}",
        "item_name": season.item_name if season else settings.SITE_NAME,
        "currency_code": settings.PAYPAL_CURRENCY,
        "invoice": str(camper.pk),
        "notify_url": request.build_absolute_uri(reverse("paypal-ipn")),
        "return": request.build_absolute_uri(reverse("your-return-view")),
        "cancel_return": request.build_absolute_uri(reverse("your-cancel-view")),
    }
    return render(
        request,
        "pay_now.html",
        {
            "form": PayPalPaymentsForm(initial=paypal_dict),
            "camper": camper,
            "season": season,
        },
    )


def return_url(request):
    """Where PayPal sends the payer after checkout.

    Purely informational. It used to run a full reconciliation pass and send
    mail, which made it an unauthenticated way to trigger database writes and
    outbound email. Payment state now changes only via the verified IPN.
    """
    return render(request, "success.html")


def canceled_url(request):
    return render(request, "cancel.html")


# ---------------------------------------------------------------------------
# Staff
# ---------------------------------------------------------------------------

class CamperLoginView(LoginView):
    """Standard Django login, with django-axes providing lockout."""

    template_name = "login.html"
    redirect_authenticated_user = True


def camper_logout(request):
    logout(request)
    return render(request, "logout.html")


def _resolve_season(slug):
    if slug:
        return get_object_or_404(CampSeason, slug=slug)
    return CampSeason.active() or CampSeason.objects.first()


@login_required
def camper_info(request, season=None):
    """Staff dashboard listing registrations for one season."""
    current = _resolve_season(season)
    if current is None:
        return render(request, "camper_info.html", {"seasons": [], "season": None})

    campers = current.campers.select_related("season")

    tab = request.GET.get("show", "paid")
    querysets = {
        "paid": campers.filter(paid=True),
        "unpaid": campers.filter(paid=False, status=Camper.Status.REGISTERED),
        "flagged": campers.filter(payment_flagged=True),
        "ineligible": campers.exclude(status=Camper.Status.REGISTERED),
    }
    selected = querysets.get(tab, querysets["paid"])

    # One aggregate query instead of evaluating the same queryset repeatedly.
    # Aliases are suffixed because an aggregate may not shadow a model field.
    totals = campers.aggregate(
        paid_n=Count("pk", filter=Q(paid=True)),
        unpaid_n=Count("pk", filter=Q(paid=False, status=Camper.Status.REGISTERED)),
        flagged_n=Count("pk", filter=Q(payment_flagged=True)),
        ineligible_n=Count("pk", filter=~Q(status=Camper.Status.REGISTERED)),
    )
    counts = {key.removesuffix("_n"): value for key, value in totals.items()}
    unique_unpaid_emails = (
        querysets["unpaid"].values("email").distinct().count()
    )

    paginator = Paginator(selected.order_by("pk"), 50)
    page = paginator.get_page(request.GET.get("page"))

    response = render(
        request,
        "camper_info.html",
        {
            "season": current,
            "seasons": CampSeason.objects.all(),
            "columns": CAMPER_COLUMNS,
            "page": page,
            "tab": tab if tab in querysets else "paid",
            "counts": counts,
            "unique_unpaid_emails": unique_unpaid_emails,
            "capacity": current.capacity,
            "admin_url": settings.ADMIN_URL,
        },
    )
    # This page renders medical notes and contact details; keep it out of caches.
    response["Cache-Control"] = "no-store, no-cache, must-revalidate, private"
    response["X-Robots-Tag"] = "noindex, nofollow"
    return response


@login_required
def camper_export(request, season):
    """CSV export of one season's registrations."""
    current = get_object_or_404(CampSeason, slug=season)
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="campers-{current.slug}.csv"'
    response["Cache-Control"] = "no-store"

    writer = csv.writer(response)
    writer.writerow([label for _, label in CAMPER_COLUMNS])
    for camper in current.campers.order_by("pk").iterator():
        writer.writerow([getattr(camper, field, "") for field, _ in CAMPER_COLUMNS])

    logger.info("User %s exported campers for %s.", request.user, current.slug)
    return response


@login_required
@require_POST
def set_registration_status(request):
    """Open or close registration for the active season.

    Stored on the season row rather than a module-level flag, so the change
    survives a restart and applies to every worker process.
    """
    current = CampSeason.active()
    if current is None:
        return redirect("camper_info")

    current.registration_open = request.POST.get("action") == "open"
    current.save(update_fields=["registration_open", "updated"])
    logger.info(
        "User %s set registration_open=%s for %s.",
        request.user, current.registration_open, current.slug,
    )
    return HttpResponseRedirect(reverse("camper_info"))


@login_required
@require_POST
def reconcile_payments(request):
    """Manual fallback that re-checks recorded IPNs against campers.

    The IPN handler is the normal path. This exists for the case where a
    notification was missed, and applies exactly the same verification rules.
    """
    from registration.services import reconcile_season

    current = CampSeason.active()
    if current is None:
        return redirect("camper_info")

    updated, flagged = reconcile_season(current)
    logger.info(
        "User %s reconciled %s: %s updated, %s flagged.",
        request.user, current.slug, updated, flagged,
    )
    return HttpResponseRedirect(reverse("camper_info"))
