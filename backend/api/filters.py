from django_filters import rest_framework as filter

from recipes.models import Ingredient, Recipe, Tag


class IngredientFilter(filter.FilterSet):

    name = filter.CharFilter(lookup_expr='istartswith')

    class Meta:
        model = Ingredient
        fields = (
            'name',
        )


class RecipeFilter(filter.FilterSet):

    tags = filter.ModelMultipleChoiceFilter(
        queryset=Tag.objects.all(),
        field_name='tags__slug',
        to_field_name='slug'
    )

    is_in_shopping_cart = filter.BooleanFilter(
        method='is_in_shopping_cart_filter'
    )

    is_favorited = filter.BooleanFilter(
        method='is_in_favs_filter'
    )

    class Meta:
        model = Recipe
        fields = (
            'author',
            'tags',
            'is_favorited',
            'is_in_shopping_cart',
        )

    def is_in_shopping_cart_filter(self, recipes, name, value):
        if value and self.request.user.is_authenticated:
            return recipes.filter(cart__user=self.request.user)
        return recipes

    def is_in_favs_filter(self, queryset, name, value):
        if value and self.request.user.is_authenticated:
            return queryset.filter(favs__user=self.request.user)
        return queryset
