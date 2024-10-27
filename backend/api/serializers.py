import base64

from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.contrib.auth.password_validation import validate_password
from django.core.files.base import ContentFile
from django.db import transaction
from rest_framework import serializers, validators, exceptions

from recipes.models import (
    FavoriteRecipe, Ingredient, Recipe, RecipeIngredient, RecipeTag,
    ShoppingCart, Tag
)
from users.models import Subscription
from users.validators import validate_username


MIN_INGREDIENT_AMOUNT = 1
ERROR_NO_INGREDIENTS = 'В рецепте должен быть хотя бы 1 ингридиент'
ERROR_INGREDIENT_DUPLICATE = 'В списке ингредиентов недопустимы повторы'
ERROR_NO_TAGS = 'У рецепта должен быть хотя бы 1 тег'
ERROR_TAG_DUPLICATE = 'В списке тэгов недопустимы повторы'
ERROR_NO_SELF_SUBSCRIPTION = 'Самоподписка не поддерживается'
ERROR_ALREADY_SUBSCRIPTED = 'Подписка уже существует'
ERROR_ALREADY_IN_CART = 'Рецепт уже в корзине'
ERROR_ALREADY_FAVED = 'Рецепт уже в избранных'


User = get_user_model()


class UserShowSerializer(serializers.ModelSerializer):

    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'avatar',
            'is_subscribed',
        )

    def get_is_subscribed(self, subscribed_to):
        user = self.context['request'].user
        if user.is_anonymous:
            return False
        return Subscription.objects.filter(
            user=user,
            subscribed_to=subscribed_to.pk
        ).exists()


class UserCreateSerializer(
    serializers.ModelSerializer,
):

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'password',
        )
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def validate_password(self, value):
        validate_password(value)
        return make_password(value)

    def validate_username(self, value):
        return validate_username(value)


class ChangePasswordSerializer(serializers.Serializer):

    current_password = serializers.CharField()
    new_password = serializers.CharField()

    def validate_new_password(self, value):
        validate_password(value)
        return make_password(value)


class Base64ImageField(serializers.ImageField):

    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name='img.' + ext)
        return super().to_internal_value(data)


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
        fields = (
            'id',
            'name',
            'slug',
        )


class IngredientSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ingredient
        fields = (
            'id',
            'name',
            'measurement_unit',
        )


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


class RecipeShortSerializer(
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


class RecipeSerializer(serializers.ModelSerializer):

    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True
    )
    author = serializers.PrimaryKeyRelatedField(
        read_only=True,
        default=serializers.CurrentUserDefault()
    )
    ingredients = RecipeIngredientSerializer(
        source="recipes_ingredients", many=True, required=False
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    image = Base64ImageField(required=True, allow_null=False)

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time',
        )
        depth = 1

    def get_is_favorited(self, recipe):
        user = self.context['request'].user
        if user.is_anonymous:
            return False
        return FavoriteRecipe.objects.filter(
            user=user,
            recipe=recipe
        ).exists()

    def get_is_in_shopping_cart(self, recipe):
        user = self.context['request'].user
        if user.is_anonymous:
            return False
        return ShoppingCart.objects.filter(
            user=user,
            recipe=recipe
        ).exists()

    def update_tags(self, recipe, tags):
        if not len(tags):
            raise exceptions.ValidationError(
                ERROR_NO_TAGS
            )
        if len(set(tags)) != len(tags):
            raise exceptions.ValidationError(
                ERROR_TAG_DUPLICATE
            )
        recipe_tags = []
        for tag in tags:
            recipe_tags.append(
                RecipeTag(recipe=recipe, tag=tag,)
            )
        RecipeTag.objects.filter(recipe=recipe).delete()
        RecipeTag.objects.bulk_create(recipe_tags)

    def update_ingredients(self, recipe, ingredients):
        if not len(ingredients):
            raise exceptions.ValidationError(
                ERROR_NO_INGREDIENTS
            )
        recipe_ingredients = []
        unique_ingredients = set()
        for ingredient in ingredients:
            id = ingredient['ingredient']['id']
            unique_ingredients.add(id)
            recipe_ingredients.append(
                RecipeIngredient(
                    recipe=recipe,
                    ingredient=id,
                    amount=ingredient['amount'],
                )
            )
        if len(unique_ingredients) != len(ingredients):
            raise exceptions.ValidationError(
                ERROR_INGREDIENT_DUPLICATE
            )
        RecipeIngredient.objects.filter(recipe=recipe).delete()
        RecipeIngredient.objects.bulk_create(recipe_ingredients)

    @transaction.atomic
    def create(self, validated_data):
        validated_data['author'] = self.context['request'].user
        ingredients = validated_data.pop('recipes_ingredients', [])
        tags = validated_data.pop('tags', [])
        recipe = Recipe.objects.create(**validated_data)
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
        data = super().to_representation(instance)
        data['author'] = UserShowSerializer(
            instance.author,
            context=self.context,
        ).data
        data["tags"] = TagSerializer(instance.tags, many=True).data
        data['ingredients'] = RecipeIngredientSerializer(
            RecipeIngredient.objects.filter(recipe=instance),
            many=True,
        ).data
        return data


class RecipeCollectionBaseSerializer(serializers.ModelSerializer):

    def to_representation(self, instance):
        data = RecipeShortSerializer(
            instance.recipe
        ).data
        return data

    class Meta:
        abstract = True


class FavoriteRecipeSerializer(
    RecipeCollectionBaseSerializer
):

    class Meta:
        model = FavoriteRecipe
        fields = (
            'user',
            'recipe',
        )
        validators = (
            validators.UniqueTogetherValidator(
                queryset=model.objects.all(),
                fields=['user', 'recipe'],
                message=ERROR_ALREADY_FAVED
            ),
        )


class ShoppingCartSerializer(
    RecipeCollectionBaseSerializer
):

    class Meta:
        model = ShoppingCart
        fields = (
            'user',
            'recipe',
        )
        validators = (
            validators.UniqueTogetherValidator(
                queryset=model.objects.all(),
                fields=['user', 'recipe'],
                message=ERROR_ALREADY_IN_CART
            ),
        )


class SubscriptionSerializer(serializers.ModelSerializer):
    user = serializers.SlugRelatedField(
        read_only=True,
        slug_field='username',
        default=serializers.CurrentUserDefault()
    )
    subscribed_to = serializers.SlugRelatedField(
        slug_field='username',
        queryset=User.objects.all(),
    )

    class Meta:
        model = Subscription
        fields = ('user', 'subscribed_to')
        validators = (
            validators.UniqueTogetherValidator(
                queryset=Subscription.objects.all(),
                fields=['user', 'subscribed_to'],
                message=ERROR_ALREADY_SUBSCRIPTED
            ),
        )

    def validate_subscribed_to(self, subscribed_to):
        user = self.context.get('request').user
        if user == subscribed_to:
            raise serializers.ValidationError(ERROR_NO_SELF_SUBSCRIPTION)
        return subscribed_to

    def to_representation(self, instance):
        data = UserShowSerializer(
            instance.subscribed_to,
            context=self.context,
        ).data
        data['recipes_count'] = Recipe.objects.filter(
            author=instance.subscribed_to
        ).count()
        recipes_limit = self.context.get(
            'request'
        ).query_params.get('recipes_limit')
        data['recipes'] = RecipeShortSerializer(
            Recipe.objects.filter(
                author=instance.subscribed_to
            )[:int(recipes_limit)],
            context=self.context,
            many=True
        ).data if recipes_limit is not None else RecipeShortSerializer(
            Recipe.objects.filter(
                author=instance.subscribed_to
            ),
            context=self.context,
            many=True
        ).data
        return data
