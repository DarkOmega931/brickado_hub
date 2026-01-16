from django.urls import path

from . import views

app_name = "decks"

urlpatterns = [
    path("", views.deck_list, name="list"),
    path("novo/", views.deck_create, name="create"),
    path("create/", views.deck_create, name="deck_create"),
    path("<int:pk>/", views.deck_detail, name="detail"),
    path("<int:pk>/delete/", views.deck_delete, name="deck_delete"),
    path("<int:pk>/import/", views.deck_import, name="deck_import"),

    # ✅ Exportar deck em TEXTO (formato oficial // Digimon DeckList)
    # Ex: 1 Elizamon                           BT24-008
    path("<int:pk>/export/", views.deck_export_text, name="deck_export"),

    # ✅ Exportar deck em IMAGEM (background + cartas)
    path("<int:pk>/export/image/", views.deck_export_image, name="deck_export_image"),
]
