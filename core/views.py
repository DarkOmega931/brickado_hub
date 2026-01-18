from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
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
    return render(request, "core/home.html", {"latest_news": latest_news})


def login_view(request):
    """
    Login simples usando AuthenticationForm.
    """
    if request.user.is_authenticated:
        return redirect("home")

    form = AuthenticationForm(request, data=request.POST or None)

    if request.method == "POST":
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, "Login realizado com sucesso!")
            next_url = request.GET.get("next")
            return redirect(next_url or "home")
        else:
            messages.error(request, "Usuário ou senha inválidos.")

    return render(request, "registration/login.html", {"form": form})


def register(request):
    """
    Cadastro padrão com UserCreationForm e login automático.
    """
    if request.user.is_authenticated:
        return redirect("home")

    form = UserCreationForm(request.POST or None)

    if request.method == "POST":
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Conta criada com sucesso!")
            return redirect("home")

    return render(request, "registration/register.html", {"form": form})


@login_required
def profile(request):
    """
    Perfil do usuário logado.
    """
    profile_obj, _ = UserProfile.objects.get_or_create(user=request.user)

    pontos = (
        LoyaltyEvent.objects.filter(user=request.user).aggregate(total=Sum("pontos"))["total"]
        or 0
    )
    total_decks = Deck.objects.filter(user=request.user).count()
    tournaments_played = 0  # placeholder
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
    Edição do perfil.
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


@login_required
def logout_view(request):
    logout(request)
    return redirect("home")
