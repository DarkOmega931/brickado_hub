# decks/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path("", views.deck_list, name="deck_list"),
    path("novo/", views.deck_create, name="deck_create"),
    path("<int:pk>/", views.deck_detail, name="deck_detail"),

    path("<int:pk>/add/", views.deck_add_card, name="deck_add_card"),
    path("<int:pk>/remove/<int:deckcard_id>/", views.deck_remove_card, name="deck_remove_card"),

    path("<int:pk>/importar/", views.deck_import, name="deck_import"),
    path("<int:pk>/export/", views.deck_export, name="deck_export"),  # ✅ novo
    path("<int:pk>/deletar/", views.deck_delete, name="deck_delete"),
]