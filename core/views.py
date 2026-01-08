from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.db.models import Sum
from django.shortcuts import redirect, render

from loyalty.models import LoyaltyEvent
from decks.models import Deck
from news.models import NewsPost

from .forms import ProfileForm
from .models import UserProfile


def home(request):
    """
    Página inicial do Brickado Hub.
    Exibe últimas notícias publicadas.
    """
    latest_news = NewsPost.objects.filter(is_published=True).order_by("-published_at")[:5]
    context = {
        "latest_news": latest_news,
    }
    return render(request, "core/home.html", context)


@login_required
def profile(request):
    """
    Perfil do usuário logado.
    Mostra pontos de fidelidade, decks e eventos recentes.
    """
    profile_obj, _ = UserProfile.objects.get_or_create(user=request.user)

    pontos_eventos = (
        LoyaltyEvent.objects.filter(user=request.user).aggregate(total=Sum("pontos"))["total"]
        or 0
    )
    pontos = pontos_eventos

    total_decks = Deck.objects.filter(user=request.user).count()
    tournaments_played = 0  # reservado para integração futura com torneios

    recent_events = LoyaltyEvent.objects.filter(user=request.user).order_by("-criado_em")[:10]

    context = {
        "profile": profile_obj,
        "pontos": pontos,
        "total_decks": total_decks,
        "tournaments_played": tournaments_played,
        "recent_events": recent_events,
    }
    return render(request, "core/profile.html", context)


@login_required
def profile_edit(request):
    """
    Tela de edição do perfil.
    Usa o ProfileForm para atualizar os dados extras.
    """
    profile_obj, _ = UserProfile.objects.get_or_create(user=request.user)

    if request.method == "POST":
        form = ProfileForm(request.POST, instance=profile_obj)
        if form.is_valid():
            form.save()
            messages.success(request, "Perfil atualizado com sucesso.")
            return redirect("profile")
    else:
        form = ProfileForm(instance=profile_obj)

    return render(request, "core/profile_edit.html", {"form": form})


def register(request):
    """
    Tela de cadastro de novo usuário.
    Usa o UserCreationForm padrão e cria o usuário na tabela auth_user.
    Depois faz login automático e redireciona para a home.
    """
    if request.user.is_authenticated:
        return redirect("home")

    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Conta criada com sucesso!")
            return redirect("home")
    else:
        form = UserCreationForm()

    return render(request, "registration/register.html", {"form": form})


@login_required
def logout_view(request):
    """
    Sai da sessão atual e volta para a home.
    (Em produção você pode preferir usar as views padrão de auth.)
    """
    logout(request)
    return redirect("home")
