from django.urls import path

from . import views

app_name = "decks"

urlpatterns = [
    path("", views.deck_list, name="deck_list"),
    path("create/", views.deck_create, name="deck_create"),
    path("<int:pk>/", views.deck_detail, name="deck_detail"),
    path("<int:pk>/delete/", views.deck_delete, name="deck_delete"),
    path("<int:pk>/import/", views.deck_import, name="deck_import"),

      # adicionar / remover carta
    path("<int:pk>/add-card/", views.deck_add_card, name="deck_add_card"),
    path("<int:pk>/remove-card/<int:deckcard_id>/", views.deck_remove_card, name="deck_remove_card"),

    # exportações
    path("<int:pk>/export-text/", views.deck_export_text, name="deck_export_text"),
    path("<int:pk>/export-image/", views.deck_export_image, name="deck_export_image"),

    # compatibilidade com o nome antigo "deck_export"
    path("<int:pk>/export/", views.deck_export_text, name="deck_export"),

    # exportações
    path("<int:pk>/export-text/", views.deck_export_text, name="deck_export_text"),
    path("<int:pk>/export-image/", views.deck_export_image, name="deck_export_image"),

    # compatibilidade com o nome antigo "deck_export"
    path("<int:pk>/export/", views.deck_export_text, name="deck_export"),

    
]
