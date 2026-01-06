# decks/services.py (ou dentro da view)
from django.db import transaction
from .decklist_io import parse_decklist_text
from .models import Deck, DeckCard  # ajuste pro seu item model


@transaction.atomic
def import_decklist_into_deck(deck: Deck, raw_text: str, mode: str = "replace"):
    """
    mode:
    - replace: apaga itens atuais e insere os do texto
    - merge: atualiza/insere mantendo os que não estiverem no texto
    """
    parsed = parse_decklist_text(raw_text)

    if mode == "replace":
        deck.cards.all().delete()

    for line in parsed:
        DeckCard.objects.update_or_create(
            deck=deck,
            cardnumber=line.cardnumber,
            defaults={"quantity": line.qty},
        )
