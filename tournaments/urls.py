from django.urls import path
from .views import (
    tournaments_home,
    tournament_detail,
    tournament_ranking,
    tournament_admin_panel,
    tournament_my_match,
    season_list,
    season_player_ranking,
    season_deck_ranking,
)

urlpatterns = [
    path("", tournaments_home, name="tournaments_home"),
    path("<int:pk>/", tournament_detail, name="tournament_detail"),
    path("<int:pk>/painel/", tournament_admin_panel, name="tournament_admin_panel"),
    path("<int:pk>/minha-partida/", tournament_my_match, name="tournament_my_match"),
    path("ranking/", tournament_ranking, name="tournament_ranking"),

    path("temporadas/", season_list, name="season_list"),
    path("temporadas/<slug:slug>/jogadores/", season_player_ranking, name="season_player_ranking"),
    path("temporadas/<slug:slug>/decks/", season_deck_ranking, name="season_deck_ranking"),
]
