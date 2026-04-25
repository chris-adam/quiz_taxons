from .models import SearchResult
from .models import Taxon
from .models import UserScore
from django.contrib import admin


@admin.register(Taxon)
class TaxonAdmin(admin.ModelAdmin):
    list_display = (
        "nom_vernaculaire",
        "genre",
        "espece",
        "famille",
        "ordre",
        "classe",
        "embranchement",
        "regne",
        "dataset",
    )
    list_filter = ("category", "dataset")
    search_fields = ("nom_vernaculaire", "genre", "espece", "famille")
    ordering = ("nom_vernaculaire",)
    readonly_fields = ("last_update",)
    fieldsets = (
        (
            "Identification",
            {
                "fields": ("nom_vernaculaire", "partie_etat_indice"),
            },
        ),
        (
            "Taxonomie",
            {
                "fields": (
                    "regne",
                    "embranchement",
                    "classe",
                    "ordre",
                    "famille",
                    "genre",
                    "espece",
                ),
            },
        ),
        (
            "Métadonnées",
            {
                "fields": ("last_update",),
            },
        ),
    )


@admin.register(SearchResult)
class SearchResultAdmin(admin.ModelAdmin):
    list_display = ("taxon", "title")
    list_filter = ("taxon",)
    search_fields = ("title", "taxon__nom_vernaculaire")
    readonly_fields = ("taxon", "title", "link", "image_context_link")
    ordering = ("taxon",)

    def has_add_permission(self, request):
        return False


@admin.register(UserScore)
class UserScoreAdmin(admin.ModelAdmin):
    list_display = ("session_id_short", "taxon", "score", "updated_at", "created_at")
    list_filter = ("created_at", "updated_at")
    search_fields = ("session_id", "taxon__nom_vernaculaire")
    readonly_fields = ("session_id", "taxon", "created_at", "updated_at")
    ordering = ("-updated_at",)
    date_hierarchy = "updated_at"

    def session_id_short(self, obj):
        return f"{obj.session_id[:12]}..."

    session_id_short.short_description = "Session ID"

    def has_add_permission(self, request):
        return False
