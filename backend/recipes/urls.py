from django.conf import settings
from django.urls import path

from .views import get_recipe


urlpatterns = [
    path(f'{settings.SHORT_RECIPE_ENDPOINT}/<int:pk>/', get_recipe),
]
