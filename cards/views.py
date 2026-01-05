from django.shortcuts import render, get_object_or_404
from .models import DigimonCard

def card_detail_by_number(request, cardnumber):
    card = get_object_or_404(DigimonCard, cardnumber__iexact=cardnumber)
    return render(request, "cards/card_detail.html", {"card": card})
