import json

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
        None,
    ),
    (
        Tag,
        'tags.json',
        None,
    )
)


class Command(BaseCommand):
    help = COMMAND_HELP

    def get_model_obj(self, model, id):
        return model.objects.get(id=id)

    def fill_model_table(
        self, model, file_name, related_fields=None, **kwargs
    ):
        with open(
            f'{kwargs["dir"]}{file_name}', 'r', encoding='utf-8'
        ) as file:
            json_data = json.load(file)
            for record in json_data:
                try:
                    if not related_fields:
                        model.objects.get_or_create(**record)
                    else:
                        fields = {}
                        for related_model, field, column in related_fields:
                            fields[field] = self.get_model_obj(
                                related_model, record.pop(column)
                            )
                        model.objects.get_or_create(**fields, **record)
                except Exception:
                    continue

    def add_arguments(self, parser):
        parser.add_argument(
            'dir', type=str, nargs='?', help=DATA_HELP, default='data/',
        )

    def handle(self, *args, **kwargs):
        for model, file_name, related_fields in JSON_PARAMS:
            self.fill_model_table(
                model, file_name, related_fields=related_fields, **kwargs
            )
