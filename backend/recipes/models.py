from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.db import models
from django.urls import reverse


MAX_TAG_NAME_LENGTH = 32
MAX_TAG_SLUG_LENGTH = 32
MAX_RECIPE_NAME_LENGTH = 256
MAX_INGRIDIENT_NAME_LENGTH = 128
MAX_MEASUREMENT_UNIT_LENGTH = 64
MIN_COOKING_TIME = 1
SELF_STR_MAX_LENGHT = 25
MAX_SHORT_URL_LENGTH = 32
ERROR_MORE_INGREDIENT = 'Количество ингридиента должно быть больше 0'
ERROR_MORE_COOKING_TIME = (
    'Приготовления не может быть короче {MIN_COOKING_TIME} мин.'
)


User = get_user_model()


class Tag(models.Model):
    name = models.CharField(
        unique=True,
        max_length=MAX_RECIPE_NAME_LENGTH,
        verbose_name='Тег',
        help_text='Введите название тега',
    )

    slug = models.SlugField(
        unique=True,
        max_length=MAX_RECIPE_NAME_LENGTH,
        verbose_name='Слаг тега',
        help_text='Введите слаг тега',
    )

    class Meta:
        ordering = ['id']
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.slug


class Ingredient(models.Model):
    name = models.CharField(
        null=False,
        blank=False,
        max_length=MAX_RECIPE_NAME_LENGTH,
        verbose_name='Ингредиент',
        help_text='Введите название ингредиента',
    )

    measurement_unit = models.CharField(
        null=False,
        blank=False,
        max_length=MAX_MEASUREMENT_UNIT_LENGTH,
        verbose_name='Единица измерения',
        help_text='Введите название единицы измерения',
    )

    class Meta:
        ordering = ['name']
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'

    def __str__(self):
        return self.name[:SELF_STR_MAX_LENGHT]


class Recipe(models.Model):
    name = models.CharField(
        null=False,
        blank=False,
        max_length=MAX_RECIPE_NAME_LENGTH,
        verbose_name='Название рецепта',
        help_text='Введите название рецепта',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор рецепта',
        help_text='Укажите автора рецепта',
        related_name='author_recipes'
    )
    tags = models.ManyToManyField(
        Tag,
        db_index=True,
        through='RecipeTag',
        verbose_name='Список тегов',
        help_text='Введите список тегов',
        related_name='tags_recipes'
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        db_index=True,
        through='RecipeIngredient',
        verbose_name='Список ингредиентов',
        help_text='Укажите ингредиенты для приготовления блюда',
        related_name='ingredients_recipes',
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
    cooking_time = models.PositiveSmallIntegerField(
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
        ordering = ['-pub_date']
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return (
            f'{self.author.username[:SELF_STR_MAX_LENGHT]}:'
            f' {self.name[:SELF_STR_MAX_LENGHT]}'
        )

    def get_absolute_url(self):
        return reverse("recipes-detail", kwargs={"pk": self.pk})


class RecipeTag(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='recipe_tags',
        verbose_name='Рецепт',
    )

    tag = models.ForeignKey(
        Tag,
        on_delete=models.CASCADE,
        related_name='recipes_with_tag',
        verbose_name='Ингридиент',
    )

    class Meta:
        verbose_name = 'Тег рецепта'
        verbose_name_plural = 'Теги рецептов'
        ordering = ('tag', 'recipe',)
        constraints = [
            models.UniqueConstraint(
                name='unique_recipe_tag',
                fields=['tag', 'recipe'],
            )
        ]

    def __str__(self):
        return (
            f'{self.recipe.name[:SELF_STR_MAX_LENGHT]}:'
            f'{self.tag.name[:SELF_STR_MAX_LENGHT]}'
        )


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='all_ingredients',
        verbose_name='Рецепт',
    )

    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='in_recipes',
        verbose_name='Ингридиент',
    )

    amount = models.PositiveIntegerField(
        verbose_name='Количество ингредиента в рецепте',
        validators=[
            MinValueValidator(
                limit_value=1,
                message=ERROR_MORE_INGREDIENT
            ),
        ],
    )

    class Meta:
        verbose_name = 'Связь ингредиента c рецептом'
        verbose_name_plural = 'Связи ингредиентов c рецептами'
        ordering = ('recipe', 'ingredient',)
        constraints = [
            models.UniqueConstraint(
                name='unique_recipe_ingredient',
                fields=['recipe', 'ingredient'],
            ),
        ]

    def __str__(self):
        return (
            f'{self.recipe.name[:SELF_STR_MAX_LENGHT]}: '
            f'{self.ingredient.name} {self.amount} '
            f'{self.ingredient.measurement_unit}'
        )


class FavoriteRecipe(models.Model):

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favs',
        verbose_name='Пользователь',
    )

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='in_favs',
        verbose_name='Рецепт',
    )

    class Meta:
        verbose_name = 'Любимый рецепт'
        verbose_name_plural = 'Любимые рецепты'
        ordering = ('user', 'recipe',)
        constraints = [
            models.UniqueConstraint(
                name='unique_favorite_record',
                fields=['user', 'recipe'],
            )
        ]

    def __str__(self):
        return (
            f'{self.user.username} длбавил в избранное '
            f'{self.recipe.name[:SELF_STR_MAX_LENGHT]}'
        )


class ShoppingCart(models.Model):

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='cart',
        verbose_name='Пользователь',
    )

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='in_carts',
        verbose_name='Рецепт',
    )

    class Meta:
        verbose_name = 'Продуктовая корзина'
        verbose_name_plural = 'Продуктовые корзины'
        ordering = ('user', 'recipe',)
        constraints = [
            models.UniqueConstraint(
                name='unique_shopping_record',
                fields=['user', 'recipe'],
            )
        ]


class RecipeLinkShortener(models.Model):

    short_url = models.CharField(
        unique=True,
        null=False,
        blank=False,
        max_length=MAX_SHORT_URL_LENGTH,
        verbose_name='Короткая ссылка',
    )

    recipe = models.OneToOneField(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
    )

    class Meta:
        verbose_name = 'Короткая ссылка на рецепт'
        verbose_name_plural = 'Коротике ссылки на рецепты'
        ordering = ('recipe',)

    def __str__(self):
        return f'{self.recipe}: {self.short_url}'
