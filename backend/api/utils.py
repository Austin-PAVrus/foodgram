def generate_shopping_file(current_time, ingredients, recipes):
    return (
        '\n'.join((
            f'{current_time.strftime("%d.%m.%Y %X %Z")}',
            'Список продуктов:',
            *[
                (
                    f'{line}. {ingredient["name"].capitalize()}: '
                    f'{ingredient["amount"]} {ingredient["measurement_unit"]}'
                ) for line, ingredient in enumerate(
                    ingredients,
                    start=1,
                )
            ],
            'для приготовления:',
            *[
                (
                    f'{line}. {recipe["name"]}'
                ) for line, recipe in enumerate(
                    recipes,
                    start=1,
                )
            ],
        ))
    )
