from __future__ import annotations

import io
import math
import requests
from PIL import Image

from django.conf import settings
from django.http import HttpResponse

from .models import Deck


# =========================
# CONFIGURAÇÕES VISUAIS
# =========================

CARD_WIDTH = 223
CARD_HEIGHT = 311
CARD_GAP_X = 14
CARD_GAP_Y = 18

MARGIN_X = 60
MARGIN_Y = 80

CARDS_PER_ROW = 10  # ajuste se quiser


# =========================
# FUNÇÕES AUXILIARES
# =========================

def fetch_card_image(cardnumber: str) -> Image.Image:
    """
    Baixa imagem da carta via CDN Digimon
    """
    url = f"https://images.digimoncard.io/images/cards/{cardnumber}.webp"
    resp = requests.get(url, timeout=10)
    resp.raise_for_status()
    img = Image.open(io.BytesIO(resp.content)).convert("RGBA")
    return img.resize((CARD_WIDTH, CARD_HEIGHT))


def load_background() -> Image.Image:
    bg_path = settings.BASE_DIR / "static" / "deck_backgrounds" / "default.png"
    return Image.open(bg_path).convert("RGBA")


# =========================
# EXPORTAÇÃO PRINCIPAL
# =========================

def export_deck_image(deck: Deck) -> Image.Image:
    """
    Gera a imagem final do deck
    """
    # lista expandida (repete conforme quantidade)
    expanded_cards: list[str] = []

    for item in deck.cards.all().order_by("cardnumber"):
        qty = int(item.quantity or 0)
        if qty <= 0:
            continue
        expanded_cards.extend([item.cardnumber.upper()] * qty)

    if not expanded_cards:
        raise ValueError("Deck vazio")

    total_cards = len(expanded_cards)
    rows = math.ceil(total_cards / CARDS_PER_ROW)

    bg = load_background()
    bg_w, bg_h = bg.size

    needed_h = (
        MARGIN_Y * 2 +
        rows * CARD_HEIGHT +
        (rows - 1) * CARD_GAP_Y
    )

    # aumenta altura se necessário
    if needed_h > bg_h:
        new_bg = Image.new("RGBA", (bg_w, needed_h), (0, 0, 0, 255))
        new_bg.paste(bg, (0, 0))
        bg = new_bg

    canvas = bg.copy()

    x = MARGIN_X
    y = MARGIN_Y

    for idx, cardnumber in enumerate(expanded_cards):
        try:
            card_img = fetch_card_image(cardnumber)
        except Exception:
            continue  # ignora carta quebrada

        canvas.alpha_composite(card_img, (x, y))

        x += CARD_WIDTH + CARD_GAP_X

        if (idx + 1) % CARDS_PER_ROW == 0:
            x = MARGIN_X
            y += CARD_HEIGHT + CARD_GAP_Y

    return canvas
