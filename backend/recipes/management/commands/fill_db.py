import json
from os import path

from django.core.management.base import BaseCommand

from ...models import (
    Ingredient, Tag
)

COMMAND_HELP = '''fill_db_from_json - заполняет базу данных
                из json-файлов указанной в параметрах директории.
                По умолчанию все файлы хранятся в директории контейнера
                data/
                '''
DATA_HELP = 'Директория с json-файлами для заполнения базы данных.'

JSON_PARAMS = (
    (
        Ingredient,
        'ingredients.json',
    ),
    (
        Tag,
        'tags.json',
    )
)


class Command(BaseCommand):
    help = COMMAND_HELP

    def get_model_obj(self, model, id):
        return model.objects.get(id=id)

    def fill_model_table(
        self, model, file_name, **kwargs
    ):
        with open(
            path.join(kwargs["dir"], file_name), 'r', encoding='utf-8'
        ) as file:
            json_data = json.load(file)
            model.objects.bulk_create(
                model(**record) for record in json_data
            )

    def add_arguments(self, parser):
        parser.add_argument(
            'dir', type=str, nargs='?', help=DATA_HELP, default='data/',
        )

    def handle(self, *args, **kwargs):
        for model, file_name in JSON_PARAMS:
            self.fill_model_table(
                model, file_name, **kwargs
            )
