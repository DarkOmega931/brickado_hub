from django.urls import path

from . import views


urlpatterns = [
    path("", views.home, name="home"),
    path("perfil/", views.profile, name="profile"),
    path("perfil/editar/", views.profile_edit, name="profile_edit"),
    path("logout/", views.logout_view, name="logout_view"),
    path("register/", views.register, name="register_core"),
]
