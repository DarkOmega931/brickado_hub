from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from core.views import home, profile, profile_edit, register

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/register/", register, name="register"),
    path("accounts/", include("django.contrib.auth.urls")),  # login/logout/password reset etc
    path("", include("core.urls")), 
    path("", home, name="home"),

    path("accounts/", include("django.contrib.auth.urls")),

    path("perfil/", profile, name="profile"),
    path("perfil/editar/", profile_edit, name="profile_edit"),

    path("fidelidade/", include("loyalty.urls")),
    path("decks/", include("decks.urls")),
    path("torneios/", include("tournaments.urls")),

    # ✅ News com namespace
    path("news/", include(("news.urls", "news"), namespace="news")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)



