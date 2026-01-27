from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("api/latest/", views.latest_article, name="latest_article"),
]
