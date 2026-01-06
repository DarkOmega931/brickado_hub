#export_image.py
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
# export_image.py
from __future__ import annotations

import io
import math

import requests
from PIL import Image

from django.conf import settings

from .models import Deck, DeckCard

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

def fetch_card_image(cardnumber: str) -> Image.Image | None:
    """
    Baixa imagem da carta via CDN Digimon.

    Retorna PIL.Image ou None se der erro.
    """
    cardnumber = (cardnumber or "").strip()
    if not cardnumber:
        return None

    url = f"https://images.digimoncard.io/images/cards/{cardnumber}.webp"

    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        img = Image.open(io.BytesIO(resp.content)).convert("RGBA")
        return img.resize((CARD_WIDTH, CARD_HEIGHT), Image.Resampling.LANCZOS)
    except Exception:
        # Se não conseguir baixar, devolve None para pular a carta
        return None


def load_background() -> Image.Image:
    """
    Tenta carregar o background em:
        static/deck_backgrounds/default.png

    Se não encontrar ou der erro, cria um fundo sólido padrão.
    """
    bg_path = settings.BASE_DIR / "static" / "deck_backgrounds" / "default.png"
    try:
        return Image.open(bg_path).convert("RGBA")
    except Exception:
        # fallback: fundo escuro 1920x1080
        return Image.new("RGBA", (1920, 1080), (0, 0, 0, 255))


# =========================
# EXPORTAÇÃO PRINCIPAL
# =========================

def export_deck_image(deck: Deck) -> Image.Image:
    """
    Gera a imagem final do deck:
    - Usa um background padrão
    - Posiciona as cartas em grid, repetindo conforme quantidade
    """

    # Monta lista expandida com base em DeckCard (modelo real)
    expanded_cards: list[str] = []

    deck_cards = (
        DeckCard.objects.filter(deck=deck)
        .select_related("card")
        .order_by("section", "codigo_carta", "nome_carta", "id")
    )

    for item in deck_cards:
        qty = int(item.quantidade or 0)
        if qty <= 0:
            continue

        # Prioriza codigo_carta; se vazio, tenta vir da FK card
        cn = (item.codigo_carta or "").strip().upper()
        if not cn and item.card_id:
            cn = (item.card.cardnumber or "").strip().upper()

        if not cn:
            continue

        # Repete a carta conforme quantidade (sem extrapolar absurdo)
        expanded_cards.extend([cn] * min(qty, 20))

    # Se não tiver cartas, só devolve o background
    if not expanded_cards:
        return load_background()

    total_cards = len(expanded_cards)
    rows = math.ceil(total_cards / CARDS_PER_ROW)

    bg = load_background()
    bg_w, bg_h = bg.size

    needed_h = (
        MARGIN_Y * 2
        + rows * CARD_HEIGHT
        + (rows - 1) * CARD_GAP_Y
    )

    # Se a altura necessária for maior que a do background, expande para baixo
    if needed_h > bg_h:
        new_bg = Image.new("RGBA", (bg_w, needed_h), (0, 0, 0, 255))
        new_bg.paste(bg, (0, 0))
        bg = new_bg
        bg_w, bg_h = bg.size

    canvas = bg.copy()

    x = MARGIN_X
    y = MARGIN_Y

    for idx, cardnumber in enumerate(expanded_cards):
        card_img = fetch_card_image(cardnumber)
        if card_img is None:
            # se não conseguir baixar essa carta, pula
            continue

        # Se por algum motivo a largura útil for menor que o necessário, corta
        if x + CARD_WIDTH > bg_w - MARGIN_X:
            # força quebra de linha
            x = MARGIN_X
            y += CARD_HEIGHT + CARD_GAP_Y

        # Se estourar verticalmente mesmo após ajuste de altura, para
        if y + CARD_HEIGHT > bg_h - MARGIN_Y:
            break

        canvas.alpha_composite(card_img, (x, y))

        x += CARD_WIDTH + CARD_GAP_X

        if (idx + 1) % CARDS_PER_ROW == 0:
            x = MARGIN_X
            y += CARD_HEIGHT + CARD_GAP_Y

    return canvas
