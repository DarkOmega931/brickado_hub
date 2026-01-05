# decks/rules.py
from __future__ import annotations

from collections import defaultdict
from typing import Dict, Iterable, Tuple

from cards.models import DigimonCard, CardCopyRule, BanlistRule, PairBanRule

# Limites globais (Digimon)
MAIN_LIMIT = 50
EGG_LIMIT = 5

DEFAULT_MAX_COPIES = 4


def is_egg_card(card: DigimonCard) -> bool:
    """
    Retorna True se a carta for Digi-Egg.
    Depende do cache no DigimonCard.card_type.
    """
    ct = (getattr(card, "card_type", "") or "").strip().lower()
    # Na sua API/model você comentou: "Digi-Egg"
    return ct in ("digi-egg", "digiegg", "digi egg", "digi-egg deck", "egg")


def get_card_limits(cardnumber: str) -> int:
    """
    Regra de cópias por cardnumber.
    - Default: 4
    - Exceções (admin): CardCopyRule.max_copies
    """
    cn = (cardnumber or "").strip()
    if not cn:
        return DEFAULT_MAX_COPIES

    rule = CardCopyRule.objects.filter(cardnumber__iexact=cn).first()
    if rule and rule.max_copies is not None:
        try:
            return int(rule.max_copies)
        except Exception:
            return DEFAULT_MAX_COPIES

    return DEFAULT_MAX_COPIES


def get_ban_limit(cardnumber: str) -> int:
    """
    Banlist por cardnumber.
    - Se não tiver regra: retorna um número grande (não limita)
    - Se tiver:
        BANNED -> 0
        LIMITED_1 -> 1
        LIMITED_2 -> 2
        ...
    """
    cn = (cardnumber or "").strip()
    if not cn:
        return 999

    rule = BanlistRule.objects.filter(cardnumber__iexact=cn).first()
    if not rule:
        return 999

    # suportando status como string ou integer (dependendo de como você modelar)
    status = getattr(rule, "status", None)

    # Caso você tenha choices tipo "BANNED", "LIMITED_1"
    if isinstance(status, str):
        s = status.upper().strip()
        if s == "BANNED":
            return 0
        if s.startswith("LIMITED_"):
            try:
                return int(s.split("_", 1)[1])
            except Exception:
                return 999
        # fallback
        return 999

    # Caso você tenha status numérico já representando max_copies
    try:
        return int(status)
    except Exception:
        return 999


def check_pair_ban(deck_cardnumbers: Iterable[str]) -> Tuple[bool, str]:
    """
    Verifica se existe pair ban no conjunto de cartas do deck.
    Retorna:
      (True, "") se OK
      (False, "mensagem") se violou
    """
    present = set((c or "").strip().upper() for c in deck_cardnumbers if c)
    if not present:
        return True, ""

    # Regras cadastradas no admin
    rules = PairBanRule.objects.all().only("card_a", "card_b")

    for r in rules:
        a = (getattr(r, "card_a", "") or "").strip().upper()
        b = (getattr(r, "card_b", "") or "").strip().upper()
        if a and b and a in present and b in present:
            return False, f"Pair ban: não pode usar {a} junto com {b}."

    return True, ""


def compute_current_counts(deck_cards) -> Tuple[int, int, Dict[str, int], Dict[str, int]]:
    """
    Recebe queryset/list de DeckCard (ideal: select_related('card')) e calcula:
    - main_total: total de cartas no MAIN (somando quantidades)
    - egg_total: total de cartas no EGG (somando quantidades)
    - cm: dict cardnumber -> qty no MAIN
    - ce: dict cardnumber -> qty no EGG
    """
    cm = defaultdict(int)
    ce = defaultdict(int)
    main_total = 0
    egg_total = 0

    for dc in deck_cards:
        qty = int(getattr(dc, "quantidade", 0) or 0)

        # pega cardnumber com prioridade:
        cn = (getattr(dc, "codigo_carta", "") or "").strip()
        if not cn and getattr(dc, "card_id", None):
            try:
                cn = (dc.card.cardnumber or "").strip()
            except Exception:
                cn = ""

        section = (getattr(dc, "section", "MAIN") or "MAIN").upper().strip()

        if section == "EGG":
            egg_total += qty
            if cn:
                ce[cn] += qty
        else:
            main_total += qty
            if cn:
                cm[cn] += qty

    return main_total, egg_total, dict(cm), dict(ce)


def validate_addition(
    *,
    section: str,
    cardnumber: str,
    qty: int,
    main_total: int,
    egg_total: int,
    cm: Dict[str, int],
    ce: Dict[str, int],
) -> Tuple[bool, str]:
    """
    Valida uma adição antes de salvar.
    Retorna (ok, mensagem_erro).
    """
    section = (section or "MAIN").upper().strip()
    cn = (cardnumber or "").strip()
    qty = int(qty or 0)

    if qty <= 0:
        return False, "Quantidade inválida."

    # Limite do deck
    if section == "EGG":
        if egg_total + qty > EGG_LIMIT:
            return False, f"Digi-Egg deck só pode ter {EGG_LIMIT} cartas no total."
    else:
        if main_total + qty > MAIN_LIMIT:
            return False, f"Main deck só pode ter {MAIN_LIMIT} cartas no total."

    # Limite por carta (min entre exceção e banlist)
    max_by_rule = get_card_limits(cn)
    max_by_ban = get_ban_limit(cn)
    max_allowed = min(max_by_rule, max_by_ban)

    if max_allowed <= 0:
        return False, f"{cn} está proibida pela banlist."

    current = (ce.get(cn, 0) if section == "EGG" else cm.get(cn, 0))
    if current + qty > max_allowed:
        return False, f"Limite excedido: {cn} permite no máximo {max_allowed} cópia(s)."

    return True, ""
