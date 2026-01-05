# cards/models.py
from __future__ import annotations

from decimal import Decimal
from django.db import models
from django.utils import timezone


class DigimonCard(models.Model):
    """
    Cache local de cartas Digimon (para não estourar rate limit da API).
    Guarde aqui o máximo de dados úteis para filtros/busca no deck builder.
    """
    cardnumber = models.CharField(max_length=32, unique=True, db_index=True)
    name = models.CharField(max_length=255, db_index=True)

    # Campos extras (vindos da API)
    card_type = models.CharField(
        max_length=50, blank=True, default="", db_index=True
    )  # Digimon, Tamer, Option, Digi-Egg
    color = models.CharField(
        max_length=80, blank=True, default="", db_index=True
    )  # "Red", "Red/Blue" etc
    color2 = models.CharField(
        max_length=80, blank=True, default="", db_index=True
    )  # opcional (se você quiser separar)

    level = models.PositiveIntegerField(null=True, blank=True, db_index=True)
    dp = models.PositiveIntegerField(null=True, blank=True, db_index=True)
    play_cost = models.PositiveIntegerField(null=True, blank=True, db_index=True)

    # Evolução (2 slots para suportar cartas com 2 requisitos)
    evo_cost_1 = models.PositiveIntegerField(null=True, blank=True)
    evo_color_1 = models.CharField(max_length=40, blank=True, default="", db_index=True)
    evo_level_1 = models.PositiveIntegerField(null=True, blank=True)

    evo_cost_2 = models.PositiveIntegerField(null=True, blank=True)
    evo_color_2 = models.CharField(max_length=40, blank=True, default="", db_index=True)
    evo_level_2 = models.PositiveIntegerField(null=True, blank=True)

    attribute = models.CharField(
        max_length=80, blank=True, default="", db_index=True
    )  # Variable, Data, Vaccine...
    digitype = models.CharField(
        max_length=120, blank=True, default="", db_index=True
    )  # Wizard...
    digitype2 = models.CharField(max_length=120, blank=True, default="", db_index=True)  # opcional
    form = models.CharField(
        max_length=80, blank=True, default="", db_index=True
    )  # Hybrid, etc (se API trouxer)

    rarity = models.CharField(max_length=40, blank=True, default="", db_index=True)
    pack = models.CharField(max_length=160, blank=True, default="", db_index=True)

    effect = models.TextField(blank=True, default="")
    inherit_effect = models.TextField(blank=True, default="")
    security_effect = models.TextField(blank=True, default="")

    image_url = models.URLField(blank=True, default="")
    last_synced_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ("cardnumber",)
        indexes = [
            models.Index(fields=["name"]),
            models.Index(fields=["cardnumber"]),
            models.Index(fields=["card_type"]),
            models.Index(fields=["color"]),
            models.Index(fields=["level"]),
            models.Index(fields=["play_cost"]),
            models.Index(fields=["dp"]),
            models.Index(fields=["attribute"]),
            models.Index(fields=["digitype"]),
            models.Index(fields=["rarity"]),
        ]

    def __str__(self) -> str:
        return f"{self.cardnumber} - {self.name}"

    @property
    def cdn_image(self) -> str:
        # Se preferir sempre usar a CDN padrão
        return f"https://images.digimoncard.io/images/cards/{self.cardnumber}.webp"


class CardPrice(models.Model):
    """
    Tabela de preços manual (admin), por cardnumber.
    Você vai alimentar via admin (unitário ou CSV).
    """
    cardnumber = models.CharField(max_length=32, unique=True, db_index=True)
    name = models.CharField(max_length=255, blank=True, default="")
    price = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    product_url = models.URLField(blank=True, default="")
    in_stock = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("cardnumber",)

    def __str__(self) -> str:
        label = self.name or self.cardnumber
        return f"{label} - R$ {self.price}"


class CardCopyRule(models.Model):
    """
    Exceções de cópias por carta (default lógico é 4, mas aqui você cadastra só as exceções).
    Ex: cardnumber X pode ter 50 cópias.
    """
    cardnumber = models.CharField(max_length=32, unique=True, db_index=True)
    max_copies = models.PositiveIntegerField(default=4)
    notes = models.CharField(max_length=255, blank=True, default="")

    class Meta:
        ordering = ("cardnumber",)

    def __str__(self) -> str:
        return f"{self.cardnumber} (max {self.max_copies})"


class BanlistRule(models.Model):
    """
    Banlist por carta.
    - BANNED = 0 cópias
    - LIMITED_1 = 1 cópia
    - LIMITED_2 = 2 cópias
    - LIMITED_3 = 3 cópias
    """
    BANNED = "BANNED"
    LIMITED_1 = "LIMITED_1"
    LIMITED_2 = "LIMITED_2"
    LIMITED_3 = "LIMITED_3"

    STATUS_CHOICES = [
        (BANNED, "Banida (0)"),
        (LIMITED_1, "Limitada a 1"),
        (LIMITED_2, "Limitada a 2"),
        (LIMITED_3, "Limitada a 3"),
    ]

    cardnumber = models.CharField(max_length=32, unique=True, db_index=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=BANNED)
    notes = models.CharField(max_length=255, blank=True, default="")

    class Meta:
        ordering = ("cardnumber",)

    def __str__(self) -> str:
        return f"{self.cardnumber} - {self.status}"

    @property
    def max_allowed(self) -> int:
        if self.status == self.BANNED:
            return 0
        if self.status == self.LIMITED_1:
            return 1
        if self.status == self.LIMITED_2:
            return 2
        if self.status == self.LIMITED_3:
            return 3
        return 0


class PairBanRule(models.Model):
    """
    Pair ban (duas cartas proibidas juntas).
    Usamos cardnumber para evitar FK quebrando se ainda não houver cache da carta.
    """
    card_a = models.CharField(max_length=32, db_index=True)
    card_b = models.CharField(max_length=32, db_index=True)
    notes = models.CharField(max_length=255, blank=True, default="")

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["card_a", "card_b"], name="uniq_pairban_a_b")
        ]
        ordering = ("card_a", "card_b")

    def __str__(self) -> str:
        return f"{self.card_a} + {self.card_b} (pair ban)"

    @staticmethod
    def normalize_pair(a: str, b: str) -> tuple[str, str]:
        a = (a or "").strip().upper()
        b = (b or "").strip().upper()
        return (a, b) if a <= b else (b, a)

    def save(self, *args, **kwargs):
        # Normaliza antes de salvar para evitar duplicidade invertida
        a, b = self.normalize_pair(self.card_a, self.card_b)
        self.card_a = a
        self.card_b = b
        super().save(*args, **kwargs)


# =========================
# Helpers para o Deck Builder
# =========================

def effective_max_copies(cardnumber: str) -> int:
    """
    Retorna o limite máximo permitido por regra de cópias.
    Default: 4, sobrescreve se existir CardCopyRule.
    """
    cn = (cardnumber or "").strip().upper()
    if not cn:
        return 4
    rule = CardCopyRule.objects.filter(cardnumber__iexact=cn).first()
    return int(rule.max_copies) if rule else 4


def effective_ban_limit(cardnumber: str) -> int | None:
    """
    Retorna limite imposto pela banlist (0/1/2/3) ou None se não houver regra.
    """
    cn = (cardnumber or "").strip().upper()
    if not cn:
        return None
    rule = BanlistRule.objects.filter(cardnumber__iexact=cn).first()
    return rule.max_allowed if rule else None


def effective_final_limit(cardnumber: str) -> int:
    """
    Limite final efetivo para adicionar carta ao deck:
    - Começa com regra de cópias (default 4 ou exceção)
    - Se existir banlist, aplica MIN(cópias, banlimit)
    Ex:
      - regra 4 e ban 1 -> 1
      - regra 50 e ban 0 -> 0
      - regra 4 e sem ban -> 4
    """
    by_copy = effective_max_copies(cardnumber)
    by_ban = effective_ban_limit(cardnumber)
    if by_ban is None:
        return by_copy
    return min(by_copy, by_ban)


def is_pair_banned(cardnumbers_in_deck: list[str], candidate: str) -> bool:
    """
    Verifica se candidate forma um par proibido com alguma carta já presente no deck.
    """
    cand = (candidate or "").strip().upper()
    if not cand:
        return False

    existing_set = {((c or "").strip().upper()) for c in cardnumbers_in_deck if c}

    # Busca regras onde candidate aparece
    qs = PairBanRule.objects.filter(
        models.Q(card_a__iexact=cand) | models.Q(card_b__iexact=cand)
    )

    for r in qs:
        a = (r.card_a or "").strip().upper()
        b = (r.card_b or "").strip().upper()
        other = b if a == cand else a
        if other in existing_set:
            return True

    return False
