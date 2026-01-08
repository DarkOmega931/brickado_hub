import re
from dataclasses import dataclass
from typing import Iterable, List


CARDNUMBER_RE = re.compile(r"^[A-Z0-9]+-\d{3}$")


@dataclass
class DecklistLine:
    qty: int
    name: str
    cardnumber: str


def parse_decklist_text(text: str) -> List[DecklistLine]:
    """
    Lê um texto no formato:

        // Digimon DeckList

        1 Elizamon                           BT24-008
        4 Dimetromon                         BT24-012

    e devolve uma lista de DecklistLine.
    Linhas em branco ou que começam com '//' são ignoradas.
    """
    lines: List[DecklistLine] = []

    for raw in (text or "").splitlines():
        line = (raw or "").strip()
        if not line:
            continue
        if line.startswith("//"):
            continue

        parts = line.split()
        if len(parts) < 3:
            continue

        qty_str = parts[0]
        try:
            qty = int(qty_str)
        except ValueError:
            continue

        cardnumber = parts[-1].strip()
        if not CARDNUMBER_RE.match(cardnumber):
            # se não bater o formato, ainda assim podemos aceitar
            # mas você pode trocar para `continue` se quiser mais rígido
            pass

        name = " ".join(parts[1:-1]).strip()

        if qty > 0 and cardnumber:
            lines.append(DecklistLine(qty=qty, name=name, cardnumber=cardnumber))

    return lines


def build_decklist_text(lines: Iterable[DecklistLine], title: str = "// Digimon DeckList") -> str:
    """
    Monta o texto padrão de decklist a partir de uma lista de DecklistLine.
    """
    lines = list(lines)
    if not lines:
        return title + "\n\n"

    max_name = max(len(dl.name or "") for dl in lines)
    body = []
    for dl in lines:
        name = dl.name or ""
        body.append(f"{dl.qty} {name:<{max_name}}  {dl.cardnumber}")

    return title + "\n\n" + "\n".join(body) + "\n"
