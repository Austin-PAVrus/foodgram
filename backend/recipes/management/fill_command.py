import json

from django.core.management.base import BaseCommand


class AbstractImportJsonCommand(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument(
            'filename',
            type=str,
            nargs='?',
            help=self.Meta.data_help,
            default=self.Meta.default_filename,
        )

    def handle(self, *args, **kwargs):
        filename = kwargs['filename']
        with open(
            filename, 'r', encoding='utf-8'
        ) as file:
            self.Meta.model.objects.bulk_create(
                (self.Meta.model(**record) for record in json.load(file)),
                ignore_conflicts=True,
            )

    class Meta:
        abstract = True
        model = None
        default_filename = ''
        data_help = ''
