from django.urls import path
from .views import card_detail_by_number

urlpatterns = [
    path("cards/<str:cardnumber>/", card_detail_by_number, name="card_detail_by_number")

]
