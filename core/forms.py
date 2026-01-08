from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import UserProfile


class RegisterForm(UserCreationForm):
    email = forms.EmailField(label="E-mail", required=True)

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")


class ProfileForm(forms.ModelForm):
    full_name = forms.CharField(label="Nome", required=False)
    phone = forms.CharField(label="Telefone / WhatsApp", required=False)
    nickname = forms.CharField(label="Nick de jogador", required=False)
    receive_news = forms.BooleanField(
        label="Quero receber novidades da Brickado por e‑mail.",
        required=False,
    )

    class Meta:
        model = UserProfile
        fields = ["full_name", "phone", "nickname", "receive_news"]
