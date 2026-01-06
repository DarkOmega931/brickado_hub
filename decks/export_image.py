# decks/export_image.py

import io
import math
from typing import Optional

import requests
from PIL import Image
from django.contrib.staticfiles import finders

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

CARDS_PER_ROW = 10  # número de cartas por linha


# =========================
# FUNÇÕES AUXILIARES
# =========================

def fetch_card_image(cardnumber: str) -> Optional[Image.Image]:
    """
    Baixa imagem da carta via CDN Digimon.
    Retorna um Image ou None se falhar.
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
        # Se der erro, devolve None e a carta é ignorada silenciosamente
        return None


def load_background() -> Image.Image:
    """
    Tenta carregar um background em static/decks/deck_bg.png.
    Se não existir ou der erro, cria um fundo simples.
    """
    bg_path = finders.find("decks/deck_bg.png")
    if bg_path:
        try:
            return Image.open(bg_path).convert("RGBA")
        except Exception:
            pass

    # fallback: fundo escuro simples 1920 x 1080
    return Image.new("RGBA", (1920, 1080), (10, 10, 10, 255))


# =========================
# EXPORTAÇÃO PRINCIPAL
# =========================

def export_deck_image(deck: Deck) -> Image.Image:
    """
    Gera a imagem final do deck:
    - Usa o background padrão
    - Organiza as cartas em grid
    - Repete a imagem da carta conforme a quantidade
    """
    bg = load_background()
    bg_w, bg_h = bg.size

    # Monta lista expandida de cardnumbers baseado em DeckCard
    expanded_cards: list[str] = []

    deck_cards = (
        DeckCard.objects.filter(deck=deck)
        .order_by("section", "codigo_carta", "id")
    )

    for item in deck_cards:
        qty = int(item.quantidade or 0)
        if qty <= 0:
            continue

        cn = (item.codigo_carta or "").strip()
        if not cn and item.card_id:
            cn = (item.card.cardnumber or "").strip()

        if not cn:
            continue

        # Repete o cardnumber conforme quantidade
        expanded_cards.extend([cn.upper()] * qty)

    if not expanded_cards:
        # Se deck estiver vazio, só devolve o background mesmo
        return bg

    total_cards = len(expanded_cards)
    rows = math.ceil(total_cards / CARDS_PER_ROW)

    # Tamanho final da carta dentro do canvas
    card_w = CARD_WIDTH
    card_h = CARD_HEIGHT

    # Calcula altura necessária
    needed_h = (
        MARGIN_Y * 2
        + rows * card_h
        + (rows - 1) * CARD_GAP_Y
    )

    # Ajusta altura do background se precisar
    if needed_h > bg_h:
        new_h = int(needed_h)
        new_bg = Image.new("RGBA", (bg_w, new_h), (10, 10, 10, 255))
        new_bg.paste(bg, (0, 0))
        bg = new_bg
        bg_w, bg_h = bg.size

    canvas = bg.copy()

    x = MARGIN_X
    y = MARGIN_Y

    for idx, cardnumber in enumerate(expanded_cards):
        card_img = fetch_card_image(cardnumber)
        if card_img is None:
            continue

        canvas.alpha_composite(card_img, (x, y))

        x += card_w + CARD_GAP_X

        # Quebra de linha
        if (idx + 1) % CARDS_PER_ROW == 0:
            x = MARGIN_X
            y += card_h + CARD_GAP_Y

        # Se passar muito do fundo, para (segurança extra)
        if y + card_h > bg_h - MARGIN_Y:
            break

    return canvas
