# decks/models.py
from django.db import models
from django.contrib.auth.models import User
from cards.models import DigimonCard


class Deck(models.Model):
    JOGO_CHOICES = [
        ("DIGIMON", "Digimon"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="decks")
    nome = models.CharField(max_length=100)
    jogo = models.CharField(max_length=20, choices=JOGO_CHOICES, default="DIGIMON")

    # usado para sugestão / agrupamento
    arquetipo = models.CharField(max_length=120, blank=True, default="")

    descricao = models.TextField(blank=True, default="")
    publico = models.BooleanField(default=False)

    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-criado_em",)

    def __str__(self):
        return f"{self.nome} ({self.jogo})"


class DeckCard(models.Model):
    SECTION_MAIN = "MAIN"
    SECTION_EGG = "EGG"

    SECTION_CHOICES = [
        (SECTION_MAIN, "Main Deck"),
        (SECTION_EGG, "Digi-Egg Deck"),
    ]

    deck = models.ForeignKey(Deck, on_delete=models.CASCADE, related_name="cartas")

    # compatibilidade com seu fluxo de import/export
    nome_carta = models.CharField(max_length=255, blank=True, default="")
    codigo_carta = models.CharField(max_length=50, blank=True, default="")
    quantidade = models.PositiveIntegerField(default=1)

    # separa deck principal (50) e egg deck (5)
    section = models.CharField(
        max_length=10,
        choices=SECTION_CHOICES,
        default=SECTION_MAIN,
        db_index=True,
    )

    # link opcional com a carta em cache da API
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
