# decks/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # Lista e criação de decks
    path("", views.deck_list, name="deck_list"),
    path("create/", views.deck_create, name="deck_create"),

    # Detalhe / excluir
    path("<int:pk>/", views.deck_detail, name="deck_detail"),
    path("<int:pk>/delete/", views.deck_delete, name="deck_delete"),

    # Manipular cartas no deck
    path("<int:pk>/add/", views.deck_add_card, name="deck_add_card"),
    path(
        "<int:pk>/remove/<int:deckcard_id>/",
        views.deck_remove_card,
        name="deck_remove_card",
    ),

    # Importar decklist em texto
    path("<int:pk>/import/", views.deck_import, name="deck_import"),

    # ✅ Exportar deck em TEXTO (formato oficial // Digimon DeckList)
    # Ex: 1 Elizamon BT24-008
    path("<int:pk>/export/", views.deck_export_text, name="deck_export"),

    # ✅ Exportar deck em IMAGEM (background + cartas)
    path(
        "<int:pk>/export/image/",
        views.deck_export_image,
        name="deck_export_image",
    ),
]