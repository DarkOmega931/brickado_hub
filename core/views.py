from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.db.models import Sum
from django.shortcuts import redirect, render
from django.contrib.auth.views import LoginView

from loyalty.models import LoyaltyEvent
from decks.models import Deck
from news.models import NewsPost

from .forms import ProfileForm
from .models import UserProfile


def home(request):
    return HttpResponse("HOME VIEW OK - VERSAO TESTE")


def login_view(request):
    return HttpResponse("LOGIN VIEW")


def logout_view(request):
    logout(request)
    return redirect("home")


def register_view(request):
    return HttpResponse("REGISTER VIEW")


@login_required
def profile_view(request):
    return HttpResponse("PROFILE VIEW")

from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect

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
