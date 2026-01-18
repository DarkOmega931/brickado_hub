from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("register/", views.register, name="register"),
    path("perfil/", views.profile, name="profile"),
    path("perfil/editar/", views.profile_edit, name="profile_edit"),
]
