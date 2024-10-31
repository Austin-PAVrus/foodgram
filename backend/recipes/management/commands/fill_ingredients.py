from ..fill_command import AbstractImportJsonCommand
from ...models import Ingredient


DEFAULT_FILENAME = 'data/ingredients.json'
COMMAND_HELP = f'''fill_tags - заполняет базу данных продукатами
                из json-файла указанной в параметрах команды.
                По умолчанию берётся файл
                {DEFAULT_FILENAME}
                '''
DATA_HELP = 'Файл json для заполнения базы данных ярлыками.'


class Command(AbstractImportJsonCommand):
    help = COMMAND_HELP

    class Meta:
        model = Ingredient
        default_filename = DEFAULT_FILENAME
        data_help = DATA_HELP
