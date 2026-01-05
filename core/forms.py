from django import forms
from .models import UserProfile

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
