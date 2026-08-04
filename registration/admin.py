from django.contrib import admin, messages

from registration.models import Camper, CampSeason
from registration.services import reconcile_season


@admin.register(CampSeason)
class CampSeasonAdmin(admin.ModelAdmin):
    list_display = (
        "name", "slug", "is_active", "registration_open",
        "starts_at", "capacity", "base_price", "registration_count",
    )
    list_filter = ("is_active", "registration_open", "theme")
    search_fields = ("name", "slug", "legacy_filter_key")
    prepopulated_fields = {"slug": ("name",)}
    actions = ("reconcile_payments",)

    fieldsets = (
        (None, {"fields": ("name", "slug", "legacy_filter_key", "theme", "is_active")}),
        ("Registration", {
            "fields": (
                "registration_open", "registration_opens_at", "registration_closes_at",
                "capacity", "base_price", "min_age", "max_age",
                "registration_deadline_note",
            )
        }),
        ("Merchandise", {
            "fields": ("merch_enabled", "merch_deadline", "hoodie_price", "mug_enabled", "mug_price")
        }),
        ("Camp", {"fields": ("starts_at", "ends_at", "venue_name", "venue_address", "venue_url")}),
        ("PayPal", {"fields": ("paypal_item_name",)}),
    )

    @admin.display(description="Paid campers")
    def registration_count(self, obj):
        return f"{obj.paid_count} / {obj.capacity}"

    @admin.action(description="Re-check PayPal payments for the selected seasons")
    def reconcile_payments(self, request, queryset):
        for season in queryset:
            updated, flagged = reconcile_season(season)
            self.message_user(
                request,
                f"{season.name}: {updated} updated, {flagged} flagged.",
                messages.WARNING if flagged else messages.SUCCESS,
            )


@admin.register(Camper)
class CamperAdmin(admin.ModelAdmin):
    list_display = (
        "id", "full_name", "email", "season", "status",
        "paid", "amount_due", "amount_paid", "payment_flagged", "created",
    )
    list_display_links = ("id", "full_name")
    list_filter = ("season", "paid", "payment_flagged", "status", "email_sent", "state")
    search_fields = ("first_name", "last_name", "email", "phone", "church", "pastor")
    date_hierarchy = "created"
    list_select_related = ("season",)
    ordering = ("-id",)
    list_per_page = 50

    # Payment state is set by the verified IPN handler, not by hand.
    readonly_fields = (
        "camp_filter", "amount_paid", "payment_note", "created", "updated", "email_sent",
    )

    fieldsets = (
        ("Camper", {
            "fields": (
                "season", "first_name", "last_name", "date_of_birth", "gender",
                "email", "phone", "city", "state",
            )
        }),
        ("Church", {"fields": ("church", "pastor", "pastor_number", "church_member", "not_married")}),
        ("Details", {"fields": ("med_notes", "tshirt_size", "swshirt_size", "mug", "region", "activity")}),
        ("Payment", {
            "fields": (
                "status", "amount_due", "amount_paid", "paid",
                "payment_flagged", "payment_note", "email_sent",
            )
        }),
        ("Record", {"fields": ("camp_filter", "created", "updated")}),
    )
