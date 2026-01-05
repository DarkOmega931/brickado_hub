from django.urls import path
from .views import loyalty_overview, reward_list

urlpatterns = [
    path("meus-pontos/", loyalty_overview, name="loyalty_overview"),
    path("resgatar/", reward_list, name="reward_list"),
]
