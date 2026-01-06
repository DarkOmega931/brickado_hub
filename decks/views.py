# decks/views.py
import io
import re
import time
import requests
from decimal import Decimal

from PIL import Image

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.staticfiles import finders
from django.db import transaction
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from .models import Deck, DeckCard
from .rules import (
    MAIN_LIMIT,
    EGG_LIMIT,
    get_card_limits,
    get_ban_limit,
    compute_current_counts,
    is_egg_card,
)

from cards.models import DigimonCard, CardPrice


# ----------------------------
# Helpers (Filtros)
# ----------------------------
def _distinct_values(qs, field: str):
    return (
        qs.exclude(**{f"{field}__isnull": True})
        .exclude(**{field: ""})
        .values_list(field, flat=True)
        .distinct()
        .order_by(field)
    )


def _apply_card_filters(base_qs, params):
    qs = base_qs

    # Busca livre
    q = (params.get("q") or "").strip()
    if q:
        qs = qs.filter(
            Q(name__icontains=q)
            | Q(cardnumber__icontains=q)
            | Q(card_type__icontains=q)
            | Q(color__icontains=q)
            | Q(pack__icontains=q)
            | Q(rarity__icontains=q)
            | Q(digitype__icontains=q)
            | Q(attribute__icontains=q)
            | Q(effect__icontains=q)
            | Q(inherit_effect__icontains=q)
            | Q(security_effect__icontains=q)
        )

    name = (params.get("name") or "").strip()
    type_ = (params.get("type") or "").strip()
    card_id = (params.get("id") or "").strip()
    level = (params.get("level") or "").strip()

    play_cost_min = (params.get("play_cost_min") or "").strip()
    play_cost_max = (params.get("play_cost_max") or "").strip()

    evolution_cost_min = (params.get("evolution_cost_min") or "").strip()
    evolution_cost_max = (params.get("evolution_cost_max") or "").strip()
    evolution_color = (params.get("evolution_color") or "").strip()

    color = (params.get("color") or "").strip()
    dp_min = (params.get("dp_min") or "").strip()
    dp_max = (params.get("dp_max") or "").strip()

    digi_type = (params.get("digi_type") or "").strip()
    attribute = (params.get("attribute") or "").strip()
    rarity = (params.get("rarity") or "").strip()
    pack = (params.get("pack") or "").strip()

    if name:
        qs = qs.filter(name__icontains=name)
    if type_:
        qs = qs.filter(card_type__iexact=type_)
    if card_id:
        qs = qs.filter(cardnumber__icontains=card_id)
    if color:
        qs = qs.filter(color__icontains=color)
    if digi_type:
        qs = qs.filter(digitype__icontains=digi_type)
    if attribute:
        qs = qs.filter(attribute__icontains=attribute)
    if rarity:
        qs = qs.filter(rarity__icontains=rarity)
    if pack:
        qs = qs.filter(pack__icontains=pack)

    # números
    if level:
        try:
            qs = qs.filter(level=int(level))
        except ValueError:
            pass

    try:
        if play_cost_min:
            qs = qs.filter(play_cost__gte=int(play_cost_min))
        if play_cost_max:
            qs = qs.filter(play_cost__lte=int(play_cost_max))
    except ValueError:
        pass

    try:
        if dp_min:
            qs = qs.filter(dp__gte=int(dp_min))
        if dp_max:
            qs = qs.filter(dp__lte=int(dp_max))
    except ValueError:
        pass

    try:
        if evolution_cost_min:
            qs = qs.filter(evo_cost_1__gte=int(evolution_cost_min))
        if evolution_cost_max:
            qs = qs.filter(evo_cost_1__lte=int(evolution_cost_max))
    except ValueError:
        pass

    if evolution_color:
        qs = qs.filter(evo_color_1__icontains=evolution_color)

    return qs


# ----------------------------
# Views principais
# ----------------------------
@login_required
def deck_list(request):
    decks = Deck.objects.filter(user=request.user).order_by("-criado_em")
    return render(request, "decks/deck_list.html", {"decks": decks})


@login_required
def deck_create(request):
    if request.method == "POST":
        nome = (request.POST.get("nome") or "").strip()
        jogo = (request.POST.get("jogo") or "DIGIMON").strip()
        arquetipo = (request.POST.get("arquetipo") or "").strip()
        descricao = (request.POST.get("descricao") or "").strip()
        publico = request.POST.get("publico") == "on"

        if not nome:
            messages.error(request, "Informe o nome do deck.")
            return render(request, "decks/deck_create.html", {})

        deck = Deck.objects.create(
            user=request.user,
            nome=nome,
            jogo=jogo,
            arquetipo=arquetipo,
            descricao=descricao,
            publico=publico,
        )
        messages.success(request, "Deck criado!")
        return redirect("deck_detail", pk=deck.id)

    return render(request, "decks/deck_create.html", {})


@login_required
def deck_delete(request, pk):
    deck = get_object_or_404(Deck, pk=pk, user=request.user)
    if request.method == "POST":
        deck.delete()
        messages.success(request, "Deck deletado.")
        return redirect("deck_list")
    return render(request, "decks/deck_confirm_delete.html", {"deck": deck})


@login_required
def deck_detail(request, pk):
    deck = get_object_or_404(Deck, pk=pk, user=request.user)

    deck_cards = (
        DeckCard.objects.filter(deck=deck)
        .select_related("card")
        .order_by("section", "id")
    )

    # ----- Busca / filtros -----
    base_qs = DigimonCard.objects.all()

    card_type_choices = list(_distinct_values(base_qs, "card_type"))
    color_choices = list(_distinct_values(base_qs, "color"))
    pack_choices = list(_distinct_values(base_qs, "pack"))
    rarity_choices = list(_distinct_values(base_qs, "rarity"))
    attribute_choices = list(_distinct_values(base_qs, "attribute"))
    digitype_choices = list(_distinct_values(base_qs, "digitype"))

    filtered = _apply_card_filters(base_qs, request.GET)
    search_results = filtered.order_by("name", "cardnumber")[:60]

    # ----- Preços -----
    price_rows = []
    total = Decimal("0.00")
    missing_prices = 0

    cardnumbers = []
    for dc in deck_cards:
        cn = (dc.codigo_carta or "").strip()
        if not cn and dc.card_id:
            cn = (dc.card.cardnumber or "").strip()
        if cn:
            cardnumbers.append(cn)

    prices = {p.cardnumber: p for p in CardPrice.objects.filter(cardnumber__in=cardnumbers)}

    for dc in deck_cards:
        qty = dc.quantidade or 1
        cn = (dc.codigo_carta or "").strip()
        name = (dc.nome_carta or "").strip()

        if dc.card_id:
            cn = cn or (dc.card.cardnumber or "")
            name = name or (dc.card.name or "")

        price_obj = prices.get(cn)
        if price_obj:
            unit = price_obj.price or Decimal("0.00")
            subtotal = unit * Decimal(qty)
            total += subtotal
            price_rows.append(
                {
                    "qty": qty,
                    "cardnumber": cn,
                    "name": name,
                    "unit": unit,
                    "subtotal": subtotal,
                    "url": price_obj.product_url,
                    "in_stock": price_obj.in_stock,
                }
            )
        else:
            missing_prices += 1
            price_rows.append(
                {
                    "qty": qty,
                    "cardnumber": cn,
                    "name": name,
                    "unit": None,
                    "subtotal": None,
                    "url": "",
                    "in_stock": True,
                }
            )

    context = {
        "deck": deck,
        "deck_cards": deck_cards,

        "search_results": search_results,
        "filters": request.GET,

        "card_type_choices": card_type_choices,
        "color_choices": color_choices,
        "pack_choices": pack_choices,
        "rarity_choices": rarity_choices,
        "attribute_choices": attribute_choices,
        "digitype_choices": digitype_choices,

        "price_rows": price_rows,
        "deck_total": total,
        "missing_prices": missing_prices,
    }
    return render(request, "decks/deck_detail.html", context)


@login_required
def deck_add_card(request, pk):
    deck = get_object_or_404(Deck, pk=pk, user=request.user)
    if request.method != "POST":
        return redirect("deck_detail", pk=deck.id)

    qty_raw = (request.POST.get("qty") or "1").strip()
    card_id = request.POST.get("card_id")

    try:
        qty = int(qty_raw)
    except ValueError:
        qty = 1
    qty = max(1, min(qty, 20))

    card = get_object_or_404(DigimonCard, pk=card_id)
    section = DeckCard.SECTION_EGG if is_egg_card(card) else DeckCard.SECTION_MAIN

    with transaction.atomic():
        deck_cards = DeckCard.objects.filter(deck=deck).select_related("card")
        main_total, egg_total, cm, ce = compute_current_counts(deck_cards)

        cn = card.cardnumber

        max_by_rule = get_card_limits(cn)
        max_by_ban = get_ban_limit(cn)
        max_allowed = min(max_by_rule, max_by_ban)

        if max_allowed <= 0:
            messages.error(request, f"{cn} está proibida pela banlist.")
            return redirect("deck_detail", pk=deck.id)

        current_copies = (ce.get(cn, 0) if section == DeckCard.SECTION_EGG else cm.get(cn, 0))
        if current_copies + qty > max_allowed:
            messages.error(request, f"Limite excedido: {cn} permite no máximo {max_allowed} cópia(s).")
            return redirect("deck_detail", pk=deck.id)

        if section == DeckCard.SECTION_EGG and egg_total + qty > EGG_LIMIT:
            messages.error(request, f"Digi-Egg deck só pode ter {EGG_LIMIT} cartas no total.")
            return redirect("deck_detail", pk=deck.id)

        if section == DeckCard.SECTION_MAIN and main_total + qty > MAIN_LIMIT:
            messages.error(request, f"Main deck só pode ter {MAIN_LIMIT} cartas no total.")
            return redirect("deck_detail", pk=deck.id)

        existing = DeckCard.objects.filter(deck=deck, section=section, card_id=card.id).first()
        if existing:
            existing.quantidade = (existing.quantidade or 0) + qty
            if not existing.codigo_carta:
                existing.codigo_carta = cn
            if not existing.nome_carta:
                existing.nome_carta = card.name
            existing.save()
        else:
            DeckCard.objects.create(
                deck=deck,
                section=section,
                quantidade=qty,
                codigo_carta=cn,
                nome_carta=card.name,
                card=card,
            )

    messages.success(request, f"Adicionado: {qty}x {card.cardnumber} {card.name} ({section})")
    return redirect("deck_detail", pk=deck.id)


@login_required
def deck_remove_card(request, pk, deckcard_id):
    deck = get_object_or_404(Deck, pk=pk, user=request.user)
    dc = get_object_or_404(DeckCard, pk=deckcard_id, deck=deck)
    dc.delete()
    messages.info(request, "Carta removida do deck.")
    return redirect("deck_detail", pk=deck.id)


# ----------------------------
# Import (Formato oficial)
# QTD  NOME DA CARTA   CARDNUMBER
# ----------------------------
@login_required
def deck_import(request, pk):
    deck = get_object_or_404(Deck, pk=pk, user=request.user)

    if request.method == "POST":
        text = (request.POST.get("decklist") or "").strip()
        replace = request.POST.get("replace") == "on"

        if not text:
            messages.error(
                request,
                "Cole a lista no formato: '4 Nome da Carta BT24-012' (qtd, nome, cardnumber).",
            )
            return redirect("deck_import", pk=deck.id)

        lines = [l.rstrip() for l in text.splitlines()]
        parsed = []

        for line in lines:
            line = (line or "").strip()
            if not line:
                continue
            if line.startswith("//"):
                continue  # ignora header

            parts = line.split()
            if len(parts) < 3:
                continue

            try:
                qty = int(parts[0])
            except ValueError:
                continue

            cardnumber = parts[-1].strip()
            name = " ".join(parts[1:-1]).strip()

            if qty > 0 and cardnumber:
                parsed.append((qty, cardnumber, name))

        if not parsed:
            messages.error(request, "Não consegui ler nenhuma linha válida. Use: 4 Nome BT24-012")
            return redirect("deck_import", pk=deck.id)

        with transaction.atomic():
            if replace:
                DeckCard.objects.filter(deck=deck).delete()

            deck_cards = DeckCard.objects.filter(deck=deck).select_related("card")
            main_total, egg_total, cm, ce = compute_current_counts(deck_cards)

            for qty, cardnumber, name in parsed:
                digicard = DigimonCard.objects.filter(cardnumber__iexact=cardnumber).first()
                section = DeckCard.SECTION_EGG if (digicard and is_egg_card(digicard)) else DeckCard.SECTION_MAIN

                max_allowed = min(get_card_limits(cardnumber), get_ban_limit(cardnumber))
                if max_allowed <= 0:
                    messages.error(request, f"{cardnumber} está proibida (banlist). Import cancelado.")
                    return redirect("deck_import", pk=deck.id)

                current_copies = (ce.get(cardnumber, 0) if section == DeckCard.SECTION_EGG else cm.get(cardnumber, 0))
                if current_copies + qty > max_allowed:
                    messages.error(request, f"Limite excedido: {cardnumber} max {max_allowed}. Import cancelado.")
                    return redirect("deck_import", pk=deck.id)

                if section == DeckCard.SECTION_EGG and egg_total + qty > EGG_LIMIT:
                    messages.error(request, f"Digi-Egg deck max {EGG_LIMIT}. Import cancelado.")
                    return redirect("deck_import", pk=deck.id)

                if section == DeckCard.SECTION_MAIN and main_total + qty > MAIN_LIMIT:
                    messages.error(request, f"Main deck max {MAIN_LIMIT}. Import cancelado.")
                    return redirect("deck_import", pk=deck.id)

                obj = DeckCard.objects.filter(deck=deck, section=section, codigo_carta__iexact=cardnumber).first()
                final_name = name or (digicard.name if digicard else "")

                if obj:
                    obj.quantidade = qty
                    obj.nome_carta = final_name or obj.nome_carta
                    obj.card = digicard or obj.card
                    obj.save()
                else:
                    DeckCard.objects.create(
                        deck=deck,
                        section=section,
                        quantidade=qty,
                        codigo_carta=cardnumber,
                        nome_carta=final_name,
                        card=digicard,
                    )

                if section == DeckCard.SECTION_EGG:
                    egg_total += qty
                    ce[cardnumber] = ce.get(cardnumber, 0) + qty
                else:
                    main_total += qty
                    cm[cardnumber] = cm.get(cardnumber, 0) + qty

        messages.success(request, f"Importação concluída: {len(parsed)} linhas processadas.")
        return redirect("deck_detail", pk=deck.id)

    return render(request, "decks/deck_import.html", {"deck": deck})


# ----------------------------
# Export TXT (Formato oficial)
# QTD  NOME DA CARTA   CARDNUMBER
# ----------------------------
@login_required
def deck_export_text(request, pk):
    deck = get_object_or_404(Deck, pk=pk, user=request.user)
    deck_cards = (
        DeckCard.objects.filter(deck=deck)
        .select_related("card")
        .order_by("section", "nome_carta", "codigo_carta")
    )

    rows = []
    for dc in deck_cards:
        qty = int(dc.quantidade or 0)
        cn = (dc.codigo_carta or "").strip()
        name = (dc.nome_carta or "").strip()

        if dc.card_id:
            cn = cn or (dc.card.cardnumber or "")
            name = name or (dc.card.name or "")

        if qty > 0 and cn:
            rows.append((qty, name, cn))

    if not rows:
        content = "// Digimon DeckList\n\n"
    else:
        max_name = max(len(n or "") for _, n, _ in rows)
        lines = [f"{qty} {name:<{max_name}}  {cn}" for qty, name, cn in rows]
        content = "// Digimon DeckList\n\n" + "\n".join(lines) + "\n"

    filename = f"{deck.nome}".replace(" ", "_").lower() + "_decklist.txt"
    response = HttpResponse(content, content_type="text/plain; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


# ----------------------------
# Export IMAGEM (background + cartas)
# ----------------------------
def _open_background_image():
    """
    Procura static/decks/deck_bg.png.
    Se não achar, cria um fundo simples.
    """
    bg_path = finders.find("decks/deck_bg.png")
    if bg_path:
        try:
            return Image.open(bg_path).convert("RGBA")
        except Exception:
            pass

    # fallback: fundo branco 1600x900
    return Image.new("RGBA", (1600, 900), (255, 255, 255, 255))


def _card_image_url(cardnumber: str) -> str:
    cn = (cardnumber or "").strip()
    if not cn:
        return ""
    # padrão da CDN
    return f"https://images.digimoncard.io/images/cards/{cn}.webp"


def _download_image(url: str, timeout=20) -> Image.Image | None:
    if not url:
        return None
    try:
        r = requests.get(url, timeout=timeout)
        r.raise_for_status()
        return Image.open(io.BytesIO(r.content)).convert("RGBA")
    except Exception:
        return None


def export_deck_image(deck: Deck) -> Image.Image:
    """
    Gera imagem do deck: background + grid de cartas (repetindo conforme quantidade).
    """
    bg = _open_background_image()

    # coleta cards repetidos
    deck_cards = (
        DeckCard.objects.filter(deck=deck)
        .select_related("card")
        .order_by("section", "codigo_carta", "nome_carta", "id")
    )

    cardnumbers = []
    for dc in deck_cards:
        qty = int(dc.quantidade or 0)
        if qty <= 0:
            continue

        cn = (dc.codigo_carta or "").strip()
        if not cn and dc.card_id:
            cn = (dc.card.cardnumber or "").strip()

        if cn:
            cardnumbers.extend([cn] * min(qty, 20))  # trava segurança

    if not cardnumbers:
        return bg

    # layout grid
    # (ajuste fino depois): margens e tamanho das cartas
    canvas_w, canvas_h = bg.size
    margin_x, margin_y = 60, 140
    gap_x, gap_y = 14, 14

    cols = 10  # ajuste para bater com seu exemplo
    card_w = (canvas_w - 2 * margin_x - (cols - 1) * gap_x) // cols
    # proporção típica carta digimon
    card_h = int(card_w * 1.4)

    x0, y0 = margin_x, margin_y

    for idx, cn in enumerate(cardnumbers):
        col = idx % cols
        row = idx // cols

        x = x0 + col * (card_w + gap_x)
        y = y0 + row * (card_h + gap_y)

        # se estourar a tela, para
        if y + card_h > canvas_h - 40:
            break

        img = _download_image(_card_image_url(cn))
        if not img:
            continue

        img = img.resize((card_w, card_h), Image.Resampling.LANCZOS)
        bg.alpha_composite(img, (x, y))

        # micro-sleep para não martelar a CDN/API
        time.sleep(0.03)

    return bg


@login_required
def deck_export_image(request, pk):
    deck = get_object_or_404(Deck, pk=pk, user=request.user)

    image = export_deck_image(deck)

    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    buffer.seek(0)

    response = HttpResponse(buffer.getvalue(), content_type="image/png")
    response["Content-Disposition"] = f'attachment; filename="deck_{deck.id}.png"'
    return response
