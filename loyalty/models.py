from django.db import models
from django.contrib.auth.models import User

class LoyaltyEvent(models.Model):
    COMPRA = "COMPRA"
    TORNEIO = "TORNEIO"
    BONUS = "BONUS"
    CHECKIN = "CHECKIN"

    TIPO_CHOICES = [
        (COMPRA, "Compra"),
        (TORNEIO, "Torneio"),
        (BONUS, "Bônus"),
        (CHECKIN, "Check-in"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="loyalty_events")
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    pontos = models.IntegerField(help_text="Use valores positivos ou negativos")
    descricao = models.CharField(max_length=255, blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        sinal = "+" if self.pontos >= 0 else ""
        return f"{self.user.username} {sinal}{self.pontos} ({self.get_tipo_display()})"

class Reward(models.Model):
    nome = models.CharField(max_length=100)
    descricao = models.CharField(max_length=255, blank=True)
    custo_pontos = models.PositiveIntegerField()
    ativo = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.nome} ({self.custo_pontos} pts)"

class RewardRedemption(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="rewards_redeemed")
    reward = models.ForeignKey(Reward, on_delete=models.CASCADE)
    pontos_usados = models.PositiveIntegerField()
    criado_em = models.DateTimeField(auto_now_add=True)
    concluido = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.user.username} -> {self.reward.nome} ({self.pontos_usados} pts)"
