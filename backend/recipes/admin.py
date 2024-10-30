from sys import maxsize

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.safestring import mark_safe

from .models import (
    FavoriteRecipe, Ingredient,
    Recipe, RecipeIngredient,
    Subscription, Tag,
    User
)


FAST_COOKING = 5
SLOW_COOKING = 60
THUMBNAIL_WIDTH = 120
THUMBNAIL_HEIGHTH = 100


class SubscribtionsFilter(admin.SimpleListFilter):

    title = 'Подписчики'
    parameter_name = 'has_subscribers_or_subscribers'

    def lookups(self, request, model_admin):

        return (
            ('has_subscribers', 'С подписчиками'),
            ('has_subscribtions', 'С подписками'),
        )

    def queryset(self, request, users):
        if self.value() == 'has_subscribtions':
            return users.filter(authors__isnull=False)
        if self.value() == 'has_subscribers':
            return users.filter(subscribers__isnull=False)
        return users


@admin.register(User)
class FoodgramUserAdmin(UserAdmin):
    list_display = (
        'username',
        'first_name',
        'last_name',
        'email',
        'thumbnail',
        'total_recipes',
        'total_subscribers',
        'total_subscriptions',
    )
    UserAdmin.fieldsets += ('Аватар', {'fields': ('avatar',)}),
    search_fields = ('username', 'email')
    list_filter = (
        SubscribtionsFilter,
    )

    @admin.display(description='Аватар')
    @mark_safe
    def thumbnail(self, user):
        if user.avatar:
            return f'<img src="{user.avatar.url}" width="120" height="100">'
        return None

    @admin.display(description='Рецепты')
    def total_recipes(self, recipe):
        return recipe.recipes.count()

    @admin.display(description='Подписки')
    def total_subscriptions(self, user):
        return user.authors.count()

    @admin.display(description='Подписчики')
    def total_subscribers(self, user):
        return user.subscribers.count()


class CookingTimeFilter(admin.SimpleListFilter):

    title = 'Время приготовления'
    parameter_name = 'cooking_time'

    cooking_time_ranges = {
        'fast': (0, FAST_COOKING),
        'medium': (FAST_COOKING + 1, SLOW_COOKING - 1),
        'slow': (SLOW_COOKING, maxsize),
    }

    def lookups(self, request, model_admin):

        fast_recipes_count = Recipe.objects.filter(
            cooking_time__range=self.cooking_time_ranges['fast']
        ).count()
        medium_recipes_count = Recipe.objects.filter(
            cooking_time__range=self.cooking_time_ranges['medium']
        ).count()
        slow_recipes_count = Recipe.objects.filter(
            cooking_time__range=self.cooking_time_ranges['slow']
        ).count()
        return (
            (
                'fast',
                f'Быстро (≤{FAST_COOKING}мин): '
                f' {fast_recipes_count}'
            ),
            (
                'medium',
                f'Средне ({FAST_COOKING + 1} - {SLOW_COOKING - 1} мин):'
                f' {medium_recipes_count}'
            ),
            (
                'slow',
                f'Долго (≥{SLOW_COOKING} мин):'
                f' {slow_recipes_count}'
            ),
        )

    def queryset(self, request, recipes):
        if (
            self.value()
            and self.value() in self.cooking_time_ranges.keys()
        ):
            return recipes.filter(
                cooking_time__range=self.cooking_time_ranges[self.value()]
            )
        return recipes


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient


class RecipeTagInline(admin.TabularInline):
    model = Recipe.tags.through


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'cooking_time',
        'author',
        'thumbnail',
        'safe_tags',
        'safe_ingredients',
        'favs_count',
    )
    list_filter = (
        'author__username',
        'tags__name',
        CookingTimeFilter
    )
    search_fields = ('name',)
    inlines = [
        RecipeIngredientInline,
    ]

    @admin.display(description='Миниатюра')
    @mark_safe
    def thumbnail(self, recipe):
        return f'<img src="{recipe.image.url}" width="120" height="100">'

    @admin.display(description='Ярлыки')
    @mark_safe
    def safe_tags(self, recipe):
        return '<br/>'.join(tag.name for tag in recipe.tags.all())

    @admin.display(description='Ингридиенты')
    @mark_safe
    def safe_ingredients(self, recipe):
        return '<br/>'.join(
            ingredient.name
            for ingredient in recipe.ingredients.all()
        )

    @admin.display(description='Добавлений в избранное')
    def favs_count(self, recipe):
        return recipe.favs.count()


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit', 'recipes_count')
    list_filter = ('measurement_unit',)
    search_fields = ('name__istartswith',)

    @admin.display(description='Вхождений в рецепты')
    def recipes_count(self, ingredient):
        return ingredient.recipes.count()


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'slug')
    list_filter = ('name',)
    search_fields = ('name__istartswith', 'slug')


admin.site.register(FavoriteRecipe)
admin.site.register(Subscription)
