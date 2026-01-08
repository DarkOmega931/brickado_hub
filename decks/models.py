from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify

from cards.models import DigimonCard


class Archetype(models.Model):
    name = models.CharField(max_length=120, unique=True, db_index=True)
    slug = models.SlugField(max_length=140, unique=True, blank=True, default="")

    class Meta:
        ordering = ("name",)

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.name) or "archetype"
            self.slug = base[:140]
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.name


class Deck(models.Model):
    JOGO_CHOICES = [
        ("DIGIMON", "Digimon"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="decks")
    nome = models.CharField(max_length=100)
    jogo = models.CharField(max_length=20, choices=JOGO_CHOICES, default="DIGIMON")

    # vínculo opcional com um arquétipo cadastrado no Admin
    arquetipo = models.ForeignKey(
        Archetype,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="decks",
        help_text="Arquetipo principal (opcional, gerenciado via Admin).",
    )

    # Campo de texto livre para compatibilidade/importações antigas
    arquetipo_nome = models.CharField(
        max_length=120,
        blank=True,
        default="",
        help_text="Nome livre do arquétipo (ex.: 'BLL AncientGreymon').",
    )

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

    deck = models.ForeignKey(Deck, on_delete=models.CASCADE, related_name="cards")

    # compatibilidade com fluxo de import/export
    nome_carta = models.CharField(max_length=255, blank=True, default="")
    codigo_carta = models.CharField(max_length=50, blank=True, default="")
    quantidade = models.PositiveIntegerField(default=1)

    # separa deck principal e egg
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

    # propriedades auxiliares p/ serviços que esperam cardnumber/quantity
    @property
    def cardnumber(self) -> str:
        return (self.codigo_carta or "").strip()

    @property
    def quantity(self) -> int:
        return int(self.quantidade or 0)
