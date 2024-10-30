from datetime import datetime
from io import BytesIO

from django.db.models import Sum

from recipes.models import Ingredient, Recipe


def generate_shopping_file(user):
    current_time = datetime.now().strftime('%d.%m.%Y %X %Z')
    ingredients = [
        '{0}. {1}: {2} {3}'.format(
            line,
            ingredient['name'].capitalize(),
            ingredient['amount'],
            ingredient['measurement_unit'],
        ) for line, ingredient in enumerate(
            Ingredient.objects.filter(
                recipes_ingredients__recipe__cart__user=user
            ).annotate(
                amount=Sum("recipes_ingredients__amount")
            ).order_by('name').values(),
            start=1,
        )
    ]
    recipes = [
        '{0}. {1}'.format(
            line,
            recipe['name'].capitalize(),
        ) for line, recipe in enumerate(
            Recipe.objects.filter(
                cart__user=user
            ).order_by('name').values('name'),
            start=1,
        )
    ]

    file_content = bytes(
        '\n'.join([
            f'{current_time}',
            'Список продуктов:',
            *ingredients,
            'для приготовления:',
            *recipes,
        ]).encode()
    )
    file = BytesIO()
    file.write(file_content)
    file.seek(0)

    return file
