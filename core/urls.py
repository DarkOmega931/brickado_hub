from django.urls import path
from .views import home, profile, profile_edit, logout_view

urlpatterns = [
    path("", home, name="home"),
    path("perfil/", profile, name="profile"),
    path("perfil/editar/", profile_edit, name="profile_edit"),
    path("logout/", logout_view, name="logout_view"),
]
