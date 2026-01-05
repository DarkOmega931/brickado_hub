from django.db import models
from django.contrib.auth.models import User
from decks.models import Deck

class Season(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=120, unique=True)
    start_date = models.DateField()
    end_date = models.DateField()
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class Tournament(models.Model):
    GAME_CHOICES = [
        ("DIGIMON", "Digimon"),
        ("LORCANA", "Lorcana"),
        ("UNION", "Union Arena"),
        ("OUTRO", "Outro TCG"),
    ]

    STATUS_CHOICES = [
        ("REGISTRATION", "Inscrições ativas"),
        ("RUNNING", "Em andamento"),
        ("FINISHED", "Finalizado"),
    ]

    name = models.CharField(max_length=150)
    game = models.CharField(max_length=20, choices=GAME_CHOICES)
    date = models.DateField()
    location = models.CharField(max_length=150, blank=True)
    description = models.TextField(blank=True)
    season = models.ForeignKey(
        Season, on_delete=models.SET_NULL, null=True, blank=True, related_name="tournaments"
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="REGISTRATION")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class TournamentPlayer(models.Model):
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE, related_name="players")
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    player_name = models.CharField(max_length=120)
    deck = models.ForeignKey(Deck, on_delete=models.SET_NULL, null=True, blank=True)
    deck_archtype_name = models.CharField(max_length=120, blank=True)
    wins = models.PositiveIntegerField(default=0)
    draws = models.PositiveIntegerField(default=0)
    losses = models.PositiveIntegerField(default=0)
    points = models.IntegerField(default=0)
    omw = models.FloatField(default=0.0, help_text="Opponents' Match Win %")
    oomw = models.FloatField(default=0.0, help_text="Opponents' Opponents' Match Win %")

    class Meta:
        unique_together = ("tournament", "player_name")
        ordering = ["-points", "-omw", "-oomw"]

    def __str__(self):
        return f"{self.player_name} @ {self.tournament.name}"
