from django.contrib.auth.models import AbstractUser
from django.db import models

from .validators import validate_username


USER_ROLE = 'user'
MODERATOR_ROLE = 'moderator'
ADMIN_ROLE = 'admin'
ROLES = (
    (USER_ROLE, 'пользователь'),
    (ADMIN_ROLE, 'администратор'),
)
MAX_USERNAME_LENGTH = 150
MAX_PASSWORD_LENGTH = 150
MAX_EMAILFIELD_LENGTH = 254


class FoodgramUser(AbstractUser):
    username = models.CharField(
        verbose_name='Юзернейм',
        max_length=MAX_USERNAME_LENGTH,
        unique=True,
        help_text='Введите юзернейм',
        validators=(
            validate_username,
        ),
    )
    email = models.EmailField(
        verbose_name='Электронная почта',
        max_length=MAX_EMAILFIELD_LENGTH,
        blank=False,
        null=False,
        unique=True,
        help_text='Введите почту'
    )
    role = models.CharField(
        verbose_name='Роль в системе',
        max_length=max(len(role) for role, _ in ROLES),
        choices=ROLES,
        default=USER_ROLE,
    )
    first_name = models.CharField(
        verbose_name='Имя',
        max_length=MAX_USERNAME_LENGTH,
        blank=False,
        null=False,
        help_text='Введите имя'
    )
    last_name = models.CharField(
        verbose_name='Фамилия',
        max_length=MAX_USERNAME_LENGTH,
        blank=False,
        null=False,
        help_text='Введите фамилию'
    )
    password = models.CharField(
        verbose_name='Пароль',
        max_length=MAX_PASSWORD_LENGTH,
    )
    avatar = models.ImageField(
        upload_to='avatars/',
        null=True,
        blank=True,
        default=None
    )

    USERNAME_FIELD = "username"
    EMAIL_FIELD = "email"
    REQUIRED_FIELDS = ("email", "first_name", "last_name")

    @property
    def is_admin(self):
        return self.role == ADMIN_ROLE or self.is_staff

    def __str__(self):
        return self.username

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('username',)


class Subscription(models.Model):
    user = models.ForeignKey(
        FoodgramUser, on_delete=models.CASCADE, related_name='subscribed_to'
    )
    subscribed_to = models.ForeignKey(
        FoodgramUser, on_delete=models.CASCADE, related_name='subscribers'
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        ordering = ('user',)
        constraints = [
            models.UniqueConstraint(
                fields=('user', 'subscribed_to',),
                name='unique_subscription'
            ),
        ]

    def __str__(self):
        return (
            f'{self.user.username} подписан на {self.subscribed_to.username}'
        )
