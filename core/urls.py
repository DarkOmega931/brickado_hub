from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),

    # Autenticação
    path("login/", views.login, name="login"),  # usa auth padrão
    path("logout/", views.logout_view, name="logout"),
    path("register/", views.register, name="register"),

    # Perfil
    path("perfil/", views.profile, name="profile"),
    path("perfil/editar/", views.profile_edit, name="profile_edit"),
]
