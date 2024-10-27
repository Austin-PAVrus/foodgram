import re

from django.core.exceptions import ValidationError

from foodgram_backend.settings import RESTRICTED_ENDPOINTS

MESSAGE_WRONG_SYMBOLS = (
    'Допустимы буквы, цифры и символы @ . + - _ .'
    ' Обнаружено: {wrong_symbols}'
)
MESSAGE_RESTRICTED_USERNAME = '"Имя {username} недопустимо'


def validate_username(value) -> str:
    wrong_symbols = re.findall(r'[^\w.@+-]', value)
    if len(wrong_symbols):
        wrong_symbols = set(wrong_symbols)
        symbols_for_message = ''.join(set(wrong_symbols))
        raise ValidationError(
            MESSAGE_WRONG_SYMBOLS.format(
                wrong_symbols=symbols_for_message
            )
        )
    if value in RESTRICTED_ENDPOINTS:
        raise ValidationError(
            MESSAGE_RESTRICTED_USERNAME.format(username=value)
        )
    return value
