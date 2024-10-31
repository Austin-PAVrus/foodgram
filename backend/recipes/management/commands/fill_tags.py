from ...models import Tag
from ..fill_command import AbstractImportJsonCommand


DEFAULT_FILENAME = 'data/tags.json'
COMMAND_HELP = '''fill_tags - заполняет базу данных ярлыками
                из json-файла указанной в параметрах команды.
                По умолчанию берётся файл
                {DEFAULT_FILENAME}
                '''
DATA_HELP = 'Файл json для заполнения базы данных ярлыками.'


class Command(AbstractImportJsonCommand):
    help = COMMAND_HELP

    class Meta:
        model = Tag
        default_filename = DEFAULT_FILENAME
        data_help = DATA_HELP
