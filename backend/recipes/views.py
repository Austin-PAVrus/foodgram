from django.conf import settings
from django.http import Http404
from django.shortcuts import redirect

from .models import Recipe


def get_recipe(request, pk):
    if Recipe.objects.filter(id=pk).exists():
        return redirect(
            request.build_absolute_uri(
                f'/{settings.FRONTEND_RECIPE_ENDPOINT}/{pk}/'
            )
        )
    raise Http404({'Recipe': pk})
