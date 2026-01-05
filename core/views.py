from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib.auth import logout
from django.db.models import Sum

from loyalty.models import LoyaltyEvent
from decks.models import Deck
from news.models import NewsPost
from .models import UserProfile
from .forms import ProfileForm

def home(request):
    latest_news = NewsPost.objects.filter(is_published=True).order_by("-published_at")[:5]
    context = {
        "latest_news": latest_news,
    }
    return render(request, "core/home.html", context)

@login_required
def profile(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    pontos_eventos = (
        LoyaltyEvent.objects.filter(user=request.user).aggregate(total=Sum("pontos"))["total"]
        or 0
    )
    pontos = pontos_eventos

    total_decks = Deck.objects.filter(user=request.user).count()
    tournaments_played = 0  # reservado para integração com torneios

    recent_events = LoyaltyEvent.objects.filter(user=request.user).order_by("-criado_em")[:10]

    context = {
        "pontos": pontos,
        "total_decks": total_decks,
        "tournaments_played": tournaments_played,
        "recent_events": recent_events,
    }
    return render(request, "core/profile.html", context)

@login_required
def profile_edit(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    if request.method == "POST":
        form = ProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            return redirect("profile")
    else:
        form = ProfileForm(instance=profile)
    return render(request, "core/profile_edit.html", {"form": form})

@login_required
def logout_view(request):
    logout(request)
    return redirect("home")
