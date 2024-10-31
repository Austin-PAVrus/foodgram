from sys import maxsize

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group
from django.db.models import Q
from django.utils.safestring import mark_safe

from .models import (
    FavoriteRecipe, Ingredient,
    Recipe, RecipeIngredient,
    ShoppingCart,
    Subscription, Tag,
    User
)


THUMBNAIL_WIDTH = 120
THUMBNAIL_HEIGHTH = 100

admin.site.unregister(Group)


class SubscribtionsRecipesFilter(admin.SimpleListFilter):

    title = 'Подписки и рецепты'
    parameter_name = 'has_recipes_has_subscribers_are_subscribed_authors'

    def lookups(self, request, model_admin):
        return (
            ('authors', 'С подписчиками'),
            ('subscribers', 'С подписками'),
            ('recipes', 'С рецептами')
        )

    def queryset(self, request, users):
        if self.value():
            return users.filter(
                ~Q(**{f'{self.value()}__isnull': False})
            ).distinct()
        return users


@admin.register(User)
class FoodgramUserAdmin(UserAdmin):
    list_display = (
        'username',
        'first_name',
        'last_name',
        'email',
        'avatar_preview',
        'total_recipes',
        'total_subscribers',
        'total_subscriptions',
    )
    UserAdmin.fieldsets += ('Аватар', {'fields': ('avatar',)}),
    search_fields = ('username', 'email')
    list_filter = (
        SubscribtionsRecipesFilter,
    )

    @admin.display(description='Аватар')
    @mark_safe
    def avatar_preview(self, user):
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

    FAST_COOKING = 5
    SLOW_COOKING = 60
    COOKING_TIME_RANGES = {
        'fast': (0, FAST_COOKING),
        'medium': (FAST_COOKING + 1, SLOW_COOKING - 1),
        'slow': (SLOW_COOKING, maxsize),
    }

    title = 'Время приготовления'
    parameter_name = 'cooking_time'

    @classmethod
    def get_filtered_recipes(cls, recipes, recipe_type):
        return recipes.filter(
            cooking_time__range=cls.COOKING_TIME_RANGES[recipe_type]
        )

    def lookups(self, request, model_admin):
        recipes_count = {
            recipe_type: self.get_filtered_recipes(
                Recipe.objects.all(),
                recipe_type,
            ).count() for recipe_type
            in self.COOKING_TIME_RANGES
        }
        return [
            (name, f'{" - ".join(map(str, range))} мин: {recipes_count[name]}')
            for name, range in self.COOKING_TIME_RANGES.items()
        ]

    def queryset(self, request, recipes):
        if self.value():
            return self.get_filtered_recipes(recipes, self.value())
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
        'tags_list',
        'ingredients_list',
        'favs_count',
    )
    list_filter = (
        'author__username',
        'tags__name',
        CookingTimeFilter
    )
    search_fields = ('name', 'tags__name',)
    inlines = [
        RecipeIngredientInline,
    ]

    @admin.display(description='Миниатюра')
    @mark_safe
    def thumbnail(self, recipe):
        return f'<img src="{recipe.image.url}" width="120" height="100">'

    @admin.display(description='Ярлыки')
    @mark_safe
    def tags_list(self, recipe):
        return '<br/>'.join(tag.name for tag in recipe.tags.all())

    @admin.display(description='Продукты')
    @mark_safe
    def ingredients_list(self, recipe):
        return '<br/>'.join(
            (
                f'{ingredient.ingredient.name}:'
                f' {ingredient.amount}'
                f' {ingredient.ingredient.measurement_unit} '
            ) for ingredient in recipe.recipes_ingredients.all()
        )

    @admin.display(description='Добавлений в избранное')
    def favs_count(self, recipe):
        return recipe.favoriterecipes.count()


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit', 'recipes_count')
    list_filter = ('measurement_unit',)
    search_fields = ('name__istartswith', 'measurement_unit')

    @admin.display(description='В рецептах')
    def recipes_count(self, ingredient):
        return ingredient.recipes.count()


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'slug', 'recipes_count')
    search_fields = ('name__istartswith', 'slug')

    @admin.display(description='В рецептах')
    def recipes_count(self, ingredient):
        return ingredient.recipes.count()


@admin.register(FavoriteRecipe)
class FavoriteRecipe(admin.ModelAdmin):
    list_display = (
        'recipe',
        'user',
    )
    search_fields = (
        'user__username',
        'recipe__name',
    )


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = (
        'recipe',
        'user',
    )
    search_fields = (
        'user__username',
        'recipe__name',
    )


@admin.register(Subscription)
class Subscription(admin.ModelAdmin):
    list_display = (
        'user',
        'author',
    )
    search_fields = (
        'user__username',
        'author__username',
    )
