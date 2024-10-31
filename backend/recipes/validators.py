import re

from django.core.exceptions import ValidationError

MESSAGE_WRONG_SYMBOLS = (
    'Допустимы буквы, цифры и символы @ . + - _ .'
    ' Обнаружено: {wrong_symbols}'
)
MESSAGE_RESTRICTED_USERNAME = '"Имя {username} недопустимо'


def validate_username(username) -> str:
    wrong_symbols = re.findall(r'[^\w.@+-]', username)
    if len(wrong_symbols):
        symbols_for_message = ''.join(set(wrong_symbols))
        raise ValidationError(
            MESSAGE_WRONG_SYMBOLS.format(
                wrong_symbols=symbols_for_message
            )
        )
    return username
