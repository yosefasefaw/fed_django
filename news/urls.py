from django.urls import path
from . import views

app_name = "news"

urlpatterns = [
    path("", views.home, name="home"),
    path("api/latest/", views.latest_article, name="latest_article"),
]
