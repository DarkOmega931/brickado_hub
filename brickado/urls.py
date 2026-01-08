from django.contrib import admin
from django.urls import include, path

from core.views import register

urlpatterns = [
    path("admin/", admin.site.urls),
    # Autenticação
    path("accounts/register/", register, name="register"),
    path("accounts/", include("django.contrib.auth.urls")),
    # Apps do projeto
    path("", include("core.urls")),
    path("fidelidade/", include("loyalty.urls")),
    path("news/", include("news.urls")),
    path("decks/", include("decks.urls")),
    path("cards/", include("cards.urls")),
    path("tournaments/", include("tournaments.urls")),
]
