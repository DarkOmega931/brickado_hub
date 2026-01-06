# decks/decklist_io.py
from __future__ import annotations

import re
from dataclasses import dataclass

CARDNUMBER_RE = re.compile(r"^[A-Z]{1,5}\d{1,3}-\d{1,3}[A-Z]?$", re.IGNORECASE)
# cobre: BT24-089, ST1-01, EX2-001, etc (ajuste se precisar)

@dataclass
class DecklistLine:
    qty: int
    name: str
    cardnumber: str


def parse_decklist_text(text: str) -> list[DecklistLine]:
    """
    Parse do formato:
    4 MetalGreymon                       BT24-015
    1 Owen Dreadnought                   BT24-082

    Regras:
    - ignora linhas vazias
    - ignora linhas começando com // (header)
    - qty = 1º token
    - cardnumber = último token
    - name = tudo entre qty e cardnumber
    """
    out: list[DecklistLine] = []

    if not text:
        return out

    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith("//"):
            continue

        # normaliza múltiplos espaços/tabs
        parts = line.split()
        if len(parts) < 3:
            continue

        # qty
        try:
            qty = int(parts[0])
        except ValueError:
            continue

        cardnumber = parts[-1].strip()
        if not CARDNUMBER_RE.match(cardnumber):
            # se quiser ser mais permissivo, remova isso
            continue

        name = " ".join(parts[1:-1]).strip()
        if not name:
            # nome pode ser vazio? normalmente não, mas vamos garantir
            name = cardnumber

        out.append(DecklistLine(qty=qty, name=name, cardnumber=cardnumber.upper()))

    return out


def build_decklist_text(lines: list[DecklistLine], title: str = "// Digimon DeckList") -> str:
    """
    Gera texto alinhado, com:
    qty + name + cardnumber
    """
    if not lines:
        return f"{title}\n\n"

    # largura do campo "qty name" pra alinhar cardnumber
    left_col = [f"{l.qty} {l.name}" for l in lines]
    pad = max(len(s) for s in left_col) + 3  # +3 espaço

    out_lines = [title, ""]
    for l in lines:
        left = f"{l.qty} {l.name}"
        out_lines.append(left.ljust(pad) + l.cardnumber)

    out_lines.append("")  # newline no fim
    return "\n".join(out_lines)
