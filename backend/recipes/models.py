from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator
from django.db import models

from .validators import validate_username

MAX_TAG_NAME_LENGTH = 32
MAX_TAG_SLUG_LENGTH = 32
MAX_RECIPE_NAME_LENGTH = 256
MAX_INGRIDIENT_NAME_LENGTH = 128
MAX_MEASUREMENT_UNIT_LENGTH = 64
MIN_COOKING_TIME = 1
MIN_INGREDIENT_AMOUNT = 1
MAX_SHORT_URL_LENGTH = 32
ERROR_MORE_INGREDIENT = (
    'Количество продукта должно быть не менее '
    f'{MIN_INGREDIENT_AMOUNT}'
)
ERROR_MORE_COOKING_TIME = (
    'Приготовления не может быть короче {MIN_COOKING_TIME} мин.'
)
STR_MAX_LENGHT = 25


MAX_USERNAME_LENGTH = 150
MAX_PASSWORD_LENGTH = 150
MAX_EMAILFIELD_LENGTH = 254


class User(AbstractUser):
    username = models.CharField(
        verbose_name='Ник',
        max_length=MAX_USERNAME_LENGTH,
        unique=True,
        help_text='Введите ник',
        validators=(
            validate_username,
        ),
    )
    email = models.EmailField(
        verbose_name='Электронная почта',
        max_length=MAX_EMAILFIELD_LENGTH,
        unique=True,
        help_text='Введите почту'
    )
    first_name = models.CharField(
        verbose_name='Имя',
        max_length=MAX_USERNAME_LENGTH,
        help_text='Введите имя'
    )
    last_name = models.CharField(
        verbose_name='Фамилия',
        max_length=MAX_USERNAME_LENGTH,
        help_text='Введите фамилию'
    )
    password = models.CharField(
        verbose_name='Пароль',
        max_length=MAX_PASSWORD_LENGTH,
    )
    avatar = models.ImageField(
        upload_to='avatars/',
        blank=True,
        null=True,
        default=None,
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ('username', 'first_name', 'last_name')

    def __str__(self):
        return self.username

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('username',)


class Subscription(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='authors'
    )
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='subscribers'
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        ordering = ('user',)
        constraints = [
            models.UniqueConstraint(
                fields=('user', 'author',),
                name='unique_subscription'
            ),
        ]

    def __str__(self):
        return (
            f'{self.user.username} подписан на {self.author.username}'
        )


class Tag(models.Model):
    name = models.CharField(
        unique=True,
        max_length=MAX_RECIPE_NAME_LENGTH,
        verbose_name='Ярлык',
        help_text='Введите название ярлыка',
    )

    slug = models.SlugField(
        unique=True,
        max_length=MAX_RECIPE_NAME_LENGTH,
        verbose_name='Идентификатор ярлыка',
        help_text='Введите идентификатор ярлыка',
    )

    class Meta:
        ordering = ['slug']
        verbose_name = 'Ярлык'
        verbose_name_plural = 'Ярлыки'

    def __str__(self):
        return self.slug


class Ingredient(models.Model):
    name = models.CharField(
        max_length=MAX_RECIPE_NAME_LENGTH,
        verbose_name='Продукт',
        help_text='Введите название продукта',
    )

    measurement_unit = models.CharField(
        max_length=MAX_MEASUREMENT_UNIT_LENGTH,
        verbose_name='Мера',
        help_text='Введите название меры',
    )

    class Meta:
        ordering = ('name',)
        verbose_name = 'Продукт'
        verbose_name_plural = 'Продукты'
        constraints = [
            models.UniqueConstraint(
                name='unique_ingridient_and_units',
                fields=['name', 'measurement_unit'],
            )
        ]

    def __str__(self):
        return self.name[:STR_MAX_LENGHT]


class Recipe(models.Model):
    name = models.CharField(
        null=False,
        blank=False,
        max_length=MAX_RECIPE_NAME_LENGTH,
        verbose_name='Название',
        help_text='Введите название',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор',
        help_text='Укажите автора',
    )
    tags = models.ManyToManyField(
        Tag,
        db_index=True,
        verbose_name='Список ярлыков',
        help_text='Введите список ярлыков',
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        db_index=True,
        through='RecipeIngredient',
        verbose_name='Список продуктов',
        help_text='Укажите продукты для приготовления блюда',
    )
    image = models.ImageField(
        upload_to='recipes/',
        null=False,
        blank=False,
        verbose_name='Изображение блюда',
        help_text='Загрузите изображение блюда',
    )
    text = models.TextField(
        null=False,
        blank=False,
        verbose_name='Описание рецепта',
        help_text='Введите описание рецепта',
    )
    cooking_time = models.PositiveIntegerField(
        null=False,
        blank=False,
        validators=[
            MinValueValidator(
                MIN_COOKING_TIME,
                ERROR_MORE_COOKING_TIME.format(
                    MIN_COOKING_TIME=MIN_COOKING_TIME
                )
            ),
        ],
        verbose_name='Время приготовления в минутах',
        help_text='Время приготовления в минутах',
    )
    pub_date = models.DateTimeField(
        db_index=True,
        auto_now_add=True,
        verbose_name='Дата публикации',
    )

    class Meta:
        ordering = ('-pub_date',)
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        default_related_name = 'recipes'

    def __str__(self):
        return (
            f'{self.author.username[:STR_MAX_LENGHT]}:'
            f' {self.name[:STR_MAX_LENGHT]}'
        )


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
    )

    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        verbose_name='Ингридиент',
    )

    amount = models.PositiveIntegerField(
        verbose_name='Мера продукта в рецепте',
        validators=[
            MinValueValidator(
                limit_value=MIN_INGREDIENT_AMOUNT,
                message=ERROR_MORE_INGREDIENT
            ),
        ],
    )

    class Meta:
        verbose_name = 'Связь продукта c рецептом'
        verbose_name_plural = 'Связи продуктов c рецептами'
        default_related_name = 'recipes_ingredients'
        ordering = ('recipe', 'ingredient',)
        constraints = [
            models.UniqueConstraint(
                name='unique_recipe_ingredient',
                fields=['recipe', 'ingredient'],
            ),
        ]

    def __str__(self):
        return (
            f'{self.recipe.name[:STR_MAX_LENGHT]}: '
            f'{self.ingredient.name} {self.amount} '
            f'{self.ingredient.measurement_unit}'
        )


class UserRecipeTemplate(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
    )

    class Meta:
        abstract = True
        ordering = ('user', 'recipe',)
        constraints = (
            models.UniqueConstraint(
                fields=('user', 'recipe',),
                name='unique_%(class)s'
            ),
        )

    def __str__(self):
        return f'{self.user.username}: {self.recipe.name[:STR_MAX_LENGHT]}'


class FavoriteRecipe(UserRecipeTemplate):

    class Meta(UserRecipeTemplate.Meta):
        verbose_name = 'Избранный рецепт'
        verbose_name_plural = 'Избранные рецепты'
        default_related_name = 'favs'


class ShoppingCart(UserRecipeTemplate):

    class Meta(UserRecipeTemplate.Meta):
        verbose_name = 'Продуктовая корзина'
        verbose_name_plural = 'Продуктовые корзины'
        default_related_name = 'cart'
