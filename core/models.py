from django.db import models
from django.contrib.auth.models import User


def avatar_upload_path(instance, filename):
    """
    Caminho para upload de avatar do usuário.
    Ex: avatars/user_1/minha_foto.png
    """
    return f"avatars/user_{instance.user_id}/{filename}"


class UserProfile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="profile",
    )
    full_name = models.CharField("Nome completo", max_length=120, blank=True)
    phone = models.CharField("Telefone / WhatsApp", max_length=30, blank=True)
    nickname = models.CharField("Nick de jogador", max_length=60, blank=True)

    avatar = models.ImageField(
        "Avatar",
        upload_to=avatar_upload_path,
        blank=True,
        null=True,
    )

    receive_news = models.BooleanField(
        "Quero receber novidades da Brickado por e-mail.",
        default=True,
    )

    def __str__(self) -> str:
        return self.full_name or self.user.username
