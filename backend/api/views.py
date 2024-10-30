from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet as DjoserUserViewSet
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import (
    AllowAny, IsAuthenticated,
)
from rest_framework.response import Response
from rest_framework.validators import ValidationError

from .filters import IngredientFilter, RecipeFilter
from .permissions import IsAuthorOrReadOnly
from .serializers import (
    IngredientSerializer,
    RecipeSerializer,
    RecipeShortSafeSerializer,
    SubscriptionSerializer,
    TagSerializer,
    UserAvatarSerializer,
)
from .utils import generate_shopping_file
from foodgram_backend.settings import (
    SELF_ENDPOINT,
    SHORT_RECIPE_ENDPOINT,
    SUBSCRIPTIONS_ENDPOINT,
)
from recipes.models import (
    FavoriteRecipe, Ingredient, Recipe, ShoppingCart, Subscription, Tag
)


ERROR_WRONG_PASSWORD = 'Вы ввели неверный пароль'
ERROR_NO_SUBSCRIPRION = 'Подписки не было'
ERROR_NO_RECIPE = 'Рецепт не найден'
ERROR_NO_SELF_SUBSCRIPTION = 'Самоподписка не поддерживается'
ERROR_ALREADY_SUBSCRIPTED = 'Подписка уже существует'
ERROR_RECIPE_ALREADY_ADDED = 'Рецепт уже добавлен'

User = get_user_model()


class UserViewSet(DjoserUserViewSet):

    queryset = User.objects.all()
    permission_classes = (AllowAny,)

    def get_permissions(self):
        if self.action == 'me':
            permissions = (IsAuthenticated,)
        else:
            permissions = self.permission_classes
        return [permission() for permission in permissions]

    @action(detail=False,
            methods=('put', 'delete'),
            url_path=SELF_ENDPOINT + '/avatar',
            permission_classes=(IsAuthenticated,)
            )
    def avatar_endpoint(self, request):
        if request.method == 'DELETE':
            user = request.user
            user.avatar = None
            user.save()
            return Response(status=HTTPStatus.NO_CONTENT)
        serializer = UserAvatarSerializer(
            request.user,
            data=request.data,
            context={'request': request},
        )
        if serializer.is_valid(raise_exception=True):
            serializer.save(user=request.user)
            return Response(serializer.data)

    @action(detail=True,
            methods=('post', 'delete'),
            permission_classes=(IsAuthenticated,),
            )
    def subscribe(self, request, id):
        user = request.user
        author = get_object_or_404(User, id=id)
        subsccription_filter = Subscription.objects.filter(
            user=user,
            author=author,
        )
        if request.method == 'DELETE':
            if subsccription_filter.delete()[0] > 0:
                return Response(status=HTTPStatus.NO_CONTENT)
            raise ValidationError({'detail': ERROR_NO_SUBSCRIPRION})
        if subsccription_filter.count() > 0:
            raise ValidationError({'detail': ERROR_ALREADY_SUBSCRIPTED})
        if author == user:
            raise ValidationError({'detail': ERROR_NO_SELF_SUBSCRIPTION})
        Subscription.objects.create(
            user=user,
            author=author
        )
        return Response(
            SubscriptionSerializer(
                author,
                context={'request': request},
            ).data,
            status=HTTPStatus.CREATED
        )

    @action(detail=False,
            methods=('get',),
            url_path=SUBSCRIPTIONS_ENDPOINT,
            permission_classes=(IsAuthenticated,),
            )
    def subscriptions(self, request):
        return self.get_paginated_response(
            SubscriptionSerializer(
                self.paginate_queryset(
                    User.objects.filter(subscribers__user=self.request.user)
                ),
                many=True,
                context={'request': request},
            ).data
        )


class TagViewSet(viewsets.ReadOnlyModelViewSet):

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    search_fields = ('name', 'slug',)
    filterset_fields = ('name', 'slug',)
    permission_classes = (AllowAny,)
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    search_fields = ('name',)
    filterset_class = IngredientFilter
    permission_classes = (AllowAny,)
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):

    queryset = Recipe.objects.all().prefetch_related()
    serializer_class = RecipeSerializer
    permission_classes = (IsAuthorOrReadOnly,)
    filterset_class = RecipeFilter

    @staticmethod
    def modify_recipe_connection(request, pk, model):
        recipe = get_object_or_404(Recipe, id=pk)
        if request.method == 'DELETE':
            if model.objects.filter(
                user=request.user,
                recipe=recipe,
            ).delete()[0] > 0:
                return Response(status=HTTPStatus.NO_CONTENT)
            raise ValidationError({'detail': ERROR_NO_RECIPE})
        if model.objects.filter(recipe=recipe).exists():
            raise ValidationError({'detail': ERROR_RECIPE_ALREADY_ADDED})
        model.objects.create(
            user=request.user,
            recipe=recipe,
        )
        return Response(
            RecipeShortSafeSerializer(
                recipe,
                context={'request': request},
            ).data,
            status=HTTPStatus.CREATED
        )

    @action(detail=True,
            methods=('post', 'delete'),
            permission_classes=(IsAuthenticated,),
            )
    def favorite(self, request, pk):
        return self.modify_recipe_connection(
            pk=pk,
            request=request,
            model=FavoriteRecipe,
        )

    @action(detail=True,
            methods=('post', 'delete'),
            permission_classes=(IsAuthenticated,),
            )
    def shopping_cart(self, request, pk):
        return self.modify_recipe_connection(
            pk=pk,
            request=request,
            model=ShoppingCart,
        )

    @action(detail=False,
            methods=('get',),
            permission_classes=(IsAuthenticated,),
            )
    def download_shopping_cart(self, request):
        user = request.user
        if not user.cart.exists():
            return Response(status=HTTPStatus.NOT_FOUND)

        return FileResponse(
            generate_shopping_file(user),
            as_attachment=True,
            filename='to_buy.txt',
        )

    @action(detail=True,
            methods=('get',),
            url_path='get-link',
            permission_classes=(AllowAny,)
            )
    def get_link(self, request, pk):
        recipe = get_object_or_404(Recipe, id=pk)
        short_url = request.build_absolute_uri(
            f'/{SHORT_RECIPE_ENDPOINT}/{recipe.id}'
        )
        return Response({'short-link': short_url}, status=HTTPStatus.OK)
