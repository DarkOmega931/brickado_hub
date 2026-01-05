from django.contrib import admin
from .models import Tournament, TournamentPlayer, Season

@admin.register(Season)
class SeasonAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "start_date", "end_date", "active")
    prepopulated_fields = {"slug": ("name",)}
    list_filter = ("active",)

class TournamentPlayerInline(admin.TabularInline):
    model = TournamentPlayer
    extra = 0

@admin.register(Tournament)
class TournamentAdmin(admin.ModelAdmin):
    list_display = ("name", "game", "date", "location", "status", "season")
    list_filter = ("game", "status", "season")
    search_fields = ("name", "location")
    inlines = [TournamentPlayerInline]

@admin.register(TournamentPlayer)
class TournamentPlayerAdmin(admin.ModelAdmin):
    list_display = (
        "player_name",
        "tournament",
        "deck_archtype_name",
        "wins",
        "draws",
        "losses",
        "points",
        "omw",
        "oomw",
    )
    list_filter = ("tournament",)
    search_fields = ("player_name", "tournament__name", "deck_archtype_name")
