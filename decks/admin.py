# decks/admin.py
from django.contrib import admin
from .models import Deck, DeckCard


@admin.register(Deck)
class DeckAdmin(admin.ModelAdmin):
    list_display = ("id", "nome", "jogo", "user", "publico", "criado_em", "atualizado_em")
    search_fields = ("nome", "arquetipo", "user__username")
    list_filter = ("jogo", "publico")
    ordering = ("-criado_em",)


@admin.register(DeckCard)
class DeckCardAdmin(admin.ModelAdmin):
    list_display = ("id", "deck", "section", "quantidade", "codigo_carta", "nome_carta", "card")
    search_fields = ("deck__nome", "codigo_carta", "nome_carta", "card__cardnumber", "card__name")
    list_filter = ("section",)
    ordering = ("deck", "section", "id")
# =========================