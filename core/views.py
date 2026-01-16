from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required

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
    # por enquanto, só redireciona pro perfil (ou renderize um template depois)
    return redirect("profile")
