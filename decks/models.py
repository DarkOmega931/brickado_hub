from __future__ import annotations

from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify

from cards.models import DigimonCard


# =========================
# Archetype (novo modelo)
# =========================
class Archetype(models.Model):
    name = models.CharField(max_length=120, unique=True, db_index=True)
    slug = models.SlugField(max_length=140, unique=True, blank=True)

    class Meta:
        ordering = ("name",)

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.name)
            self.slug = base[:140] if base else slugify(f"archetype-{self.pk}")
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


# =========================
# Deck
# =========================
class Deck(models.Model):
    JOGO_CHOICES = [
        ("DIGIMON", "Digimon"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="decks")
    nome = models.CharField(max_length=100)
    jogo = models.CharField(max_length=20, choices=JOGO_CHOICES, default="DIGIMON")

    # 🔁 substitui o antigo CharField
    archetype = models.ForeignKey(
        Archetype,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="decks",
    )

    descricao = models.TextField(blank=True, default="")
    publico = models.BooleanField(default=False)

    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-criado_em",)

    def __str__(self):
        return f"{self.nome} ({self.jogo})"


# =========================
# DeckCard
# =========================
class DeckCard(models.Model):
    SECTION_MAIN = "MAIN"
    SECTION_EGG = "EGG"

    SECTION_CHOICES = [
        (SECTION_MAIN, "Main Deck"),
        (SECTION_EGG, "Digi-Egg Deck"),
    ]

    deck = models.ForeignKey(
        Deck,
        on_delete=models.CASCADE,
        related_name="cartas",
    )

    nome_carta = models.CharField(max_length=255, blank=True, default="")
    codigo_carta = models.CharField(max_length=50, blank=True, default="")
    quantidade = models.PositiveIntegerField(default=1)

    section = models.CharField(
        max_length=10,
        choices=SECTION_CHOICES,
        default=SECTION_MAIN,
        db_index=True,
    )

    card = models.ForeignKey(
        DigimonCard,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="in_decks",
    )

    class Meta:
        ordering = ("section", "id")
        indexes = [
            models.Index(fields=["deck", "section"]),
            models.Index(fields=["deck", "codigo_carta"]),
            models.Index(fields=["deck", "card"]),
        ]

    def __str__(self):
        code = self.codigo_carta or (self.card.cardnumber if self.card_id else "")
        name = self.nome_carta or (self.card.name if self.card_id else "")
        return f"{self.quantidade}x {code} {name} [{self.deck.nome}]"
