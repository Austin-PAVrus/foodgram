from django.contrib import admin

from .models import (
    FavoriteRecipe, Ingredient, Tag,
    Recipe, RecipeIngredient, RecipeTag, RecipeLinkShortener
)


class RecipeTagInline(admin.TabularInline):
    model = RecipeTag


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient


class RecipeLinkShortenerInLine(admin.TabularInline):
    model = RecipeLinkShortener


class RecipeAdmin(admin.ModelAdmin):
    list_display = ('name', 'author', 'favs_count',)
    list_filter = ('author', 'name', 'tags',)
    search_fields = ('name',)
    inlines = [
        RecipeTagInline, RecipeIngredientInline, RecipeLinkShortenerInLine
    ]
    exclude = ('ingredients',)

    def favs_count(self, obj):
        return obj.in_favs.count()

    favs_count.short_description = 'Добавлений в избранное'


class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit',)
    list_filter = ('name',)
    search_fields = ('name__istartswith',)


class TagAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'slug')
    list_filter = ('name',)
    search_fields = ('name__istartswith', 'slug')


admin.site.register(Recipe, RecipeAdmin)
admin.site.register(Ingredient, IngredientAdmin)
admin.site.register(FavoriteRecipe)
admin.site.register(Tag, TagAdmin)
