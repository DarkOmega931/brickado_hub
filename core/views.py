# core/views.py
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.db.models import Sum
from django.shortcuts import render, redirect

from loyalty.models import LoyaltyEvent
from decks.models import Deck
from news.models import NewsPost

from .forms import ProfileForm
from .models import UserProfile


def home(request):
    if request.user.is_authenticated:
        loyalty_summary = (
            LoyaltyEvent.objects
            .filter(user=request.user)
            .aggregate(total_points=Sum("points"))
        )
        total_points = loyalty_summary["total_points"] or 0

        last_events = (
            LoyaltyEvent.objects
            .filter(user=request.user)
            .order_by("-created_at")[:5]
        )
        decks = (
            Deck.objects
            .filter(user=request.user)
            .order_by("-updated_at")[:5]
        )
    else:
        total_points = 0
        last_events = LoyaltyEvent.objects.none()
        decks = Deck.objects.none()

    news = NewsPost.objects.order_by("-created_at")[:5]

    context = {
        "total_points": total_points,
        "recent_loyalty_events": last_events,
        "recent_decks": decks,
        "news_list": news,
    }
    return render(request, "core/home.html", context)


@login_required
def profile(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)

    if request.method == "POST":
        form = ProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Perfil atualizado com sucesso!")
            return redirect("profile")
    else:
        form = ProfileForm(instance=profile)

    return render(request, "core/profile.html", {"form": form})


@login_required
def loyalty_history(request):
    events = (
        LoyaltyEvent.objects
        .filter(user=request.user)
        .order_by("-created_at")
    )
    return render(request, "core/loyalty_history.html", {"events": events})


@login_required
def loyalty_overview(request):
    summary = (
        LoyaltyEvent.objects
        .filter(user=request.user)
        .aggregate(total_points=Sum("points"))
    )
    total_points = summary["total_points"] or 0
    events = (
        LoyaltyEvent.objects
        .filter(user=request.user)
        .order_by("-created_at")[:10]
    )

    return render(
        request,
        "core/loyalty_overview.html",
        {"total_points": total_points, "recent_events": events},
    )


def register(request):
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
    logout(request)
    return redirect("home")
