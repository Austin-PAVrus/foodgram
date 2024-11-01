from sys import maxsize

from django.contrib.auth import get_user_model
from django.db import transaction
from djoser.serializers import UserSerializer as DjoserUserSerializer
from drf_extra_fields.fields import Base64ImageField
from rest_framework import exceptions, serializers

from recipes.models import (
    FavoriteRecipe,
    ERROR_MORE_INGREDIENT,
    Ingredient,
    MIN_INGREDIENT_AMOUNT,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
    Subscription,
    Tag
)

from recipes.validators import validate_username

MIN_INGREDIENTS_COUNT = 1
ERROR_NO_INGREDIENTS = (
    f'Минимальное число продуктов в рецепте: {MIN_INGREDIENTS_COUNT}'
)
ERROR_NO_TAGS = 'У рещепта должны быть ярлыки'
ERROR_DUPLICATE = 'Обнаружены дупликаты: {duplicates}'
ERROR_ALREADY_IN_CART = 'Рецепт уже в корзине'
ERROR_ALREADY_FAVED = 'Рецепт уже в избранных'
ERROR_RECIPE_LIMIT_NOT_INT = 'recipe_limit должно быть целым числом'
ERROR_EMPTY_BASE64IMAGE = 'Поле image не может быть пустым'
TAG = 'Ярлык'
INGREDIENT = 'Продукт'


User = get_user_model()


def CalculateFilterObjectExists(model, user, **kwargs):
    return (
        not user.is_anonymous
        and model.objects.filter(
            user=user,
            **kwargs,
        ).exists()
    )


class UserSerializer(DjoserUserSerializer):

    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            *DjoserUserSerializer.Meta.fields,
            'is_subscribed',
            'avatar',
        )

    def validate_username(self, username):
        return validate_username(username)

    def get_is_subscribed(self, author):
        return CalculateFilterObjectExists(
            model=Subscription,
            user=self.context['request'].user,
            author=author
        )


class UserAvatarSerializer(serializers.ModelSerializer):

    avatar = Base64ImageField(required=True, allow_null=False)

    class Meta:
        model = User
        fields = (
            'avatar',
        )


class TagSerializer(serializers.ModelSerializer):

    class Meta:
        model = Tag
        fields = '__all__'


class IngredientSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ingredient
        fields = '__all__'


class RecipeIngredientSerializer(serializers.ModelSerializer):

    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(),
        source='ingredient.id',
    )
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = RecipeIngredient
        fields = (
            'id',
            'name',
            'measurement_unit',
            'amount',
        )

    def validate_amount(self, amount):
        if amount < MIN_INGREDIENT_AMOUNT:
            raise ValueError({
                {'detail': ERROR_MORE_INGREDIENT}
            })
        return amount


class RecipeShortSafeSerializer(
    serializers.ModelSerializer
):

    class Meta:
        model = Recipe
        fields = (
            'id',
            'name',
            'image',
            'cooking_time',
        )


class RecipeSafeSerializer(
    RecipeShortSafeSerializer
):
    tags = TagSerializer(many=True)
    author = UserSerializer()
    ingredients = RecipeIngredientSerializer(
        source='recipes_ingredients', many=True, required=False
    )
    is_in_shopping_cart = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField()

    class Meta(RecipeShortSafeSerializer.Meta):
        fields = (
            *RecipeShortSafeSerializer.Meta.fields,
            'author',
            'tags',
            'text',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
        )

    def get_is_favorited(self, recipe):
        return CalculateFilterObjectExists(
            model=FavoriteRecipe,
            user=self.context['request'].user,
            recipe=recipe,
        )

    def get_is_in_shopping_cart(self, recipe):
        return CalculateFilterObjectExists(
            model=ShoppingCart,
            user=self.context['request'].user,
            recipe=recipe,
        )


class RecipeSerializer(serializers.ModelSerializer):

    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
    )
    author = serializers.PrimaryKeyRelatedField(
        read_only=True,
        default=serializers.CurrentUserDefault()
    )
    ingredients = RecipeIngredientSerializer(
        source='recipes_ingredients', many=True, required=False
    )
    image = Base64ImageField(required=True, allow_null=False)

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'name',
            'image',
            'text',
            'cooking_time',
        )

    @staticmethod
    def find_duplicates(items, item_type):
        duplicates = {item for item in items if items.count(item) > 1}
        if duplicates:
            raise serializers.ValidationError(
                {item_type: ERROR_DUPLICATE.format(duplicates=duplicates)}
            )

    def validate_image(self, image):
        if not image:
            raise serializers.ValidationError({
                'detail': ERROR_EMPTY_BASE64IMAGE
            })
        return image

    def update_tags(self, recipe, tags):
        if not tags:
            raise exceptions.ValidationError(
                ERROR_NO_TAGS
            )
        self.find_duplicates(tags, TAG)
        recipe.tags.clear()
        recipe.tags.set(tags)

    def update_ingredients(self, recipe, ingredients):
        if not ingredients:
            raise exceptions.ValidationError(
                ERROR_NO_INGREDIENTS
            )
        ingredients_ids = [
            ingredient['ingredient']['id'] for ingredient in ingredients
        ]
        self.find_duplicates(ingredients_ids, INGREDIENT)
        ingredients_to_delete = set(
            Ingredient.objects.filter(recipes_ingredients__recipe=recipe)
        ) - set(ingredients_ids)
        for ingredient in ingredients_to_delete:
            RecipeIngredient.objects.filter(
                recipe=recipe,
                ingredient=ingredient,
            ).delete()
        RecipeIngredient.objects.bulk_create([
            RecipeIngredient(
                recipe=recipe,
                ingredient=ingredient['ingredient']['id'],
                amount=ingredient['amount'],
            ) for ingredient in ingredients],
            ignore_conflicts=True
        )

    @transaction.atomic
    def create(self, validated_data):
        validated_data['author'] = self.context['request'].user
        ingredients = validated_data.pop('recipes_ingredients', [])
        tags = validated_data.pop('tags', [])
        recipe = super().create(validated_data)
        self.update_tags(recipe, tags)
        self.update_ingredients(recipe, ingredients)
        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        validated_data['author'] = self.context['request'].user
        ingredients = validated_data.pop('recipes_ingredients', [])
        tags = validated_data.pop('tags', [])
        self.update_tags(instance, tags)
        self.update_ingredients(instance, ingredients)
        return super().update(instance, validated_data)

    def to_representation(self, instance):
        return RecipeSafeSerializer(
            instance,
            context=self.context,
        ).data


class SubscriptionSerializer(UserSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta(UserSerializer.Meta):
        fields = (
            *UserSerializer.Meta.fields,
            'recipes',
            'recipes_count'
        )

    def get_recipes(self, user):
        try:
            recipes_limit = int(
                self.context.get(
                    'request'
                ).query_params.get('recipes_limit', maxsize)
            )
        except ValueError:
            raise serializers.ValidationError(
                {'detail': ERROR_RECIPE_LIMIT_NOT_INT}
            )
        return RecipeShortSafeSerializer(
            user.recipes.all()[:recipes_limit],
            context=self.context,
            many=True
        ).data

    def get_recipes_count(self, user):
        return user.recipes.count()
