import io
import time
from typing import List, Optional

import requests
from PIL import Image
from django.contrib.staticfiles import finders

from .models import Deck, DeckCard


CARD_GRID_COLUMNS = 10
MARGIN_X = 60
MARGIN_Y = 140
GAP_X = 14
GAP_Y = 14
CARD_ASPECT = 1.4  # altura ~ 1.4x largura


def _open_background_image() -> Image.Image:
    """
    Procura static/decks/deck_bg.png.
    Se não achar, cria um fundo simples 1600x900 branco.
    """
    bg_path = finders.find("decks/deck_bg.png")
    if bg_path:
        try:
            return Image.open(bg_path).convert("RGBA")
        except Exception:
            pass

    return Image.new("RGBA", (1600, 900), (255, 255, 255, 255))


def _card_image_url(cardnumber: str) -> str:
    cn = (cardnumber or "").strip()
    if not cn:
        return ""
    # padrão da CDN do Digimon Card Game
    return f"https://images.digimoncard.io/images/cards/{cn}.webp"


def _download_card_image(url: str, timeout: int = 20) -> Optional[Image.Image]:
    if not url:
        return None
    try:
        resp = requests.get(url, timeout=timeout)
        resp.raise_for_status()
        return Image.open(io.BytesIO(resp.content)).convert("RGBA")
    except Exception:
        return None


def export_deck_image(deck: Deck) -> Image.Image:
    """
    Gera imagem do deck: background + grid de cartas (repetindo conforme quantidade).
    Usa deck_bg.png como fundo se existir em static/decks/.
    """
    bg = _open_background_image()

    deck_cards = (
        DeckCard.objects.filter(deck=deck)
        .select_related("card")
        .order_by("section", "codigo_carta", "nome_carta", "id")
    )

    cardnumbers: List[str] = []
    for dc in deck_cards:
        qty = int(dc.quantidade or 0)
        if qty <= 0:
            continue

        cn = (dc.codigo_carta or "").strip()
        if not cn and dc.card_id:
            cn = (dc.card.cardnumber or "").strip()

        if cn:
            # proteção para não inflar muito a imagem
            cardnumbers.extend([cn] * min(qty, 20))

    if not cardnumbers:
        return bg

    # Layout de grid
    canvas_w, canvas_h = bg.size
    cols = CARD_GRID_COLUMNS

    card_w = (canvas_w - 2 * MARGIN_X - (cols - 1) * GAP_X) // cols
    card_h = int(card_w * CARD_ASPECT)

    x0, y0 = MARGIN_X, MARGIN_Y

    for idx, cn in enumerate(cardnumbers):
        col = idx % cols
        row = idx // cols

        x = x0 + col * (card_w + GAP_X)
        y = y0 + row * (card_h + GAP_Y)

        # se estourar verticalmente, para
        if y + card_h > canvas_h - 40:
            break

        img = _download_card_image(_card_image_url(cn))
        if not img:
            continue

        img = img.resize((card_w, card_h), Image.Resampling.LANCZOS)
        bg.alpha_composite(img, (x, y))

        # micro pausa para não martelar a CDN
        time.sleep(0.03)

    return bg
