from datetime import datetime


def generate_content(ingredients, recipes):
    current_time = datetime.now()
    return '\n'.join((
        f'{current_time.strftime("%d.%m.%Y %X %Z")}',
        'Список продуктов:',
        *[
            '{0}. {1}: {2} ({3})'.format(
                line,
                ingredient['name'].capitalize(),
                ingredient['amount'],
                ingredient['measurement_unit'],
            ) for line, ingredient in enumerate(
                ingredients,
                start=1,
            )
        ],
        'для приготовления:',
        *[
            f'{line}. {recipe["name"]}'
            for line, recipe in enumerate(
                recipes,
                start=1,
            )
        ],
    ))
