from django.urls import path
from .views import home, profile, profile_edit, logout_view

urlpatterns = [
    path("", views.home, name="home"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("register/", views.register_view, name="register"),
    path("perfil/", views.profile_view, name="profile"),
]
