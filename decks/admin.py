from django.contrib import admin

from .models import Deck, DeckCard, Archetype


@admin.register(Archetype)
class ArchetypeAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}


class DeckCardInline(admin.TabularInline):
    model = DeckCard
    extra = 0
    fields = ("section", "quantidade", "codigo_carta", "nome_carta", "card")
    readonly_fields = ()
    autocomplete_fields = ("card",)


@admin.register(Deck)
class DeckAdmin(admin.ModelAdmin):
    list_display = ("nome", "user", "jogo", "publico", "criado_em")
    list_filter = ("jogo", "publico", "criado_em")
    search_fields = ("nome", "arquetipo__name", "arquetipo_nome", "user__username")
    inlines = [DeckCardInline]
