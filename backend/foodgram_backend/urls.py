from django.contrib import admin
from django.urls import include, path

from api.views import redirect_from_recipe_short_url
from .settings import SHORT_RECIPE_ENDPOINT

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    path(
        f'{SHORT_RECIPE_ENDPOINT}/<str:short_url>/',
        redirect_from_recipe_short_url
    ),
]
