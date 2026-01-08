from django.shortcuts import render, get_object_or_404

from .models import DigimonCard


def card_list(request):
    """Lista todas as cartas para navegação simples."""
    cards = DigimonCard.objects.all().order_by("name")
    return render(request, "cards/card_list.html", {"cards": cards})


def card_detail(request, cardnumber):
    """Detalhe de uma carta específica pelo cardnumber (ex: BT24-008)."""
    card = get_object_or_404(DigimonCard, cardnumber=cardnumber)
    return render(request, "cards/card_detail.html", {"card": card})


def card_detail_by_number(request, cardnumber):
    """Alias compatível para imports antigos: mesmo comportamento de card_detail."""
    return card_detail(request, cardnumber)
