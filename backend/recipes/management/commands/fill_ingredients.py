import json

from django.core.management.base import BaseCommand

from ...models import Ingredient

DEFAULT_FILENAME = 'data/ingredients.json'
COMMAND_HELP = f'''fill_tags - заполняет базу данных продукатами
                из json-файла указанной в параметрах команды.
                По умолчанию берётся файл
                {DEFAULT_FILENAME}
                '''
DATA_HELP = 'Файл json для заполнения базы данных ярлыками.'


class Command(BaseCommand):
    help = COMMAND_HELP

    def add_arguments(self, parser):
        parser.add_argument(
            'filename',
            type=str,
            nargs='?',
            help=DATA_HELP,
            default=DEFAULT_FILENAME,
        )

    def handle(self, *args, **kwargs):
        filename = kwargs['filename']
        with open(
            filename, 'r', encoding='utf-8'
        ) as file:
            Ingredient.objects.bulk_create(
                (Ingredient(**record) for record in json.load(file)),
                ignore_conflicts=True,
            )
