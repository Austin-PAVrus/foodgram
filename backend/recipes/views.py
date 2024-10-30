from django.shortcuts import redirect

from foodgram_backend.settings import FRONTEND_RECIPE_ENDPOINT


def get_recipe(request, pk):
    return redirect(
        request.build_absolute_uri(
            f'/{FRONTEND_RECIPE_ENDPOINT}/{pk}/'
        )
    )
