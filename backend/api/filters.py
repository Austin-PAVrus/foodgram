from django_filters import rest_framework as filter

from recipes.models import Ingredient, Tag, Recipe


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

    def is_in_shopping_cart_filter(self, queryset, name, value):
        if value and self.request.user.is_authenticated:
            return queryset.filter(in_carts__user=self.request.user)
        return queryset

    def is_in_favs_filter(self, queryset, name, value):
        if value and self.request.user.is_authenticated:
            return queryset.filter(in_favs__user=self.request.user)
        return queryset
