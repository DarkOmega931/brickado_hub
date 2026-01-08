from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List

from .models import Deck, DeckCard
from .decklist_io import DecklistLine, parse_decklist_text, build_decklist_text


@dataclass
class ImportResult:
    deck: Deck
    lines: List[DecklistLine]
    replaced: bool


def import_decklist_into_deck(deck: Deck, text: str, replace: bool = False) -> ImportResult:
    """
    Converte um texto de decklist no formato:
        4 Nome da Carta BT24-012
    em registros DeckCard vinculados ao `deck`.
    """
    lines = parse_decklist_text(text)

    if not lines:
        return ImportResult(deck=deck, lines=[], replaced=False)

    if replace:
        deck.cards.all().delete()

    for line in lines:
        DeckCard.objects.update_or_create(
            deck=deck,
            codigo_carta=line.cardnumber,
            defaults={
                "quantidade": line.qty,
                "nome_carta": line.name,
            },
        )

    return ImportResult(deck=deck, lines=lines, replaced=replace)


def export_deck_to_text(deck: Deck) -> str:
    """
    Exporta o deck para o texto de decklist oficial.
    """
    lines: List[DecklistLine] = []

    qs = deck.cards.order_by("section", "codigo_carta", "nome_carta", "id").select_related("card")
    for dc in qs:
        qty = int(dc.quantidade or 0)
        if qty <= 0:
            continue

        cn = (dc.codigo_carta or "").strip()
        if not cn and dc.card_id:
            cn = (dc.card.cardnumber or "").strip()

        name = (dc.nome_carta or "").strip()
        if not name and dc.card_id:
            name = (dc.card.name or "").strip()

        if qty and cn:
            lines.append(
                DecklistLine(
                    qty=qty,
                    name=name or "",
                    cardnumber=cn,
                )
            )

    return build_decklist_text(lines)
