from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Sum, Count, Avg
from django.utils import timezone

from .models import Tournament, TournamentPlayer, Season


def tournaments_home(request):
    tournaments = Tournament.objects.all().order_by("-date")
    return render(request, "tournaments/tournaments_home.html", {"tournaments": tournaments})


def tournament_detail(request, pk):
    tournament = get_object_or_404(Tournament, pk=pk)

    standings = TournamentPlayer.objects.filter(tournament=tournament).order_by(
        "-points", "-omw", "-oomw", "player_name"
    )

    players_count = standings.count()

    return render(
        request,
        "tournaments/tournament_detail.html",
        {
            "tournament": tournament,
            "standings": standings,
            "players_count": players_count,
        },
    )


def tournament_ranking(request):
    # Ranking geral por jogador (somando resultados de todos os torneios)
    results = (
        TournamentPlayer.objects.values("player_name")
        .annotate(
            tournaments_played=Count("id"),
            total_points=Sum("points"),
            total_wins=Sum("wins"),
            total_draws=Sum("draws"),
            total_losses=Sum("losses"),
            avg_omw=Avg("omw"),
            avg_oomw=Avg("oomw"),
        )
        .order_by("-total_points", "-total_wins", "player_name")
    )

    # Ranking de decks por arquétipo (somando uso + pontos)
    deck_stats = (
        TournamentPlayer.objects.exclude(deck_archtype_name="")
        .values("deck_archtype_name")
        .annotate(
            total_uses=Count("id"),
            sum_points=Sum("points"),
            sum_wins=Sum("wins"),
            sum_draws=Sum("draws"),
            sum_losses=Sum("losses"),
        )
        .order_by("-total_uses", "-sum_points", "deck_archtype_name")
    )

    return render(
        request,
        "tournaments/tournament_ranking.html",
        {
            "results": results,
            "deck_stats": deck_stats,
        },
    )


@login_required
def tournament_admin_panel(request, pk):
    """
    Painel admin simples para o torneio (sem rounds/matches).
    Serve para:
      - Encerrar inscrições (mudar status)
      - Forçar status RUNNING/FINISHED
      - Recalcular standings (caso você edite pontos no admin)
    """
    tournament = get_object_or_404(Tournament, pk=pk)

    if not request.user.is_staff:
        messages.error(request, "Apenas administradores podem acessar este painel.")
        return redirect("tournament_detail", pk=tournament.pk)

    if request.method == "POST":
        action = request.POST.get("action", "").strip()

        if action == "close_registration":
            tournament.status = "RUNNING"
            tournament.save()
            messages.success(request, "Inscrições encerradas. Torneio marcado como EM ANDAMENTO.")
            return redirect("tournament_admin_panel", pk=tournament.pk)

        if action == "finish":
            tournament.status = "FINISHED"
            tournament.save()
            messages.success(request, "Torneio finalizado.")
            return redirect("tournament_admin_panel", pk=tournament.pk)

        if action == "recalc":
            # Se você lança resultados via admin, isso não “calcula rounds” (porque não existe),
            # mas mantém o painel útil pra reordenar e conferir standings.
            messages.success(request, "Standings atualizados (ordenação aplicada).")
            return redirect("tournament_admin_panel", pk=tournament.pk)

        messages.warning(request, "Ação inválida.")
        return redirect("tournament_admin_panel", pk=tournament.pk)

    players = TournamentPlayer.objects.filter(tournament=tournament).order_by("player_name")
    standings = TournamentPlayer.objects.filter(tournament=tournament).order_by(
        "-points", "-omw", "-oomw", "player_name"
    )

    return render(
        request,
        "tournaments/tournament_admin_panel.html",
        {
            "tournament": tournament,
            "players": players,
            "standings": standings,
        },
    )


@login_required
def tournament_my_match(request, pk):
    """
    No seu modelo atual (sem Match/Round), não existe “minha partida”.
    Então deixamos uma tela segura pra não quebrar o app.
    """
    tournament = get_object_or_404(Tournament, pk=pk)
    return render(
        request,
        "tournaments/tournament_my_match.html",
        {
            "tournament": tournament,
            "info": "Ainda não existe sistema de rodadas/pareamentos neste modelo atual.",
        },
    )


# -------------------------
# Temporadas (Season)
# -------------------------

def season_list(request):
    seasons = Season.objects.all().order_by("-start_date")
    return render(request, "tournaments/season_list.html", {"seasons": seasons})


def season_player_ranking(request, slug):
    season = get_object_or_404(Season, slug=slug)

    qs = TournamentPlayer.objects.filter(
        tournament__date__gte=season.start_date,
        tournament__date__lte=season.end_date,
    )

    results = (
        qs.values("player_name")
        .annotate(
            tournaments_played=Count("id"),
            total_points=Sum("points"),
            total_wins=Sum("wins"),
            total_draws=Sum("draws"),
            total_losses=Sum("losses"),
            avg_omw=Avg("omw"),
            avg_oomw=Avg("oomw"),
        )
        .order_by("-total_points", "-total_wins", "player_name")
    )

    return render(
        request,
        "tournaments/season_player_ranking.html",
        {"season": season, "results": results},
    )


def season_deck_ranking(request, slug):
    season = get_object_or_404(Season, slug=slug)

    qs = TournamentPlayer.objects.filter(
        tournament__date__gte=season.start_date,
        tournament__date__lte=season.end_date,
    ).exclude(deck_archtype_name="")

    deck_stats = (
        qs.values("deck_archtype_name")
        .annotate(
            total_uses=Count("id"),
            sum_points=Sum("points"),
            sum_wins=Sum("wins"),
            sum_draws=Sum("draws"),
            sum_losses=Sum("losses"),
        )
        .order_by("-total_uses", "-sum_points", "deck_archtype_name")
    )

    return render(
        request,
        "tournaments/season_deck_ranking.html",
        {"season": season, "deck_stats": deck_stats},
    )
