from datetime import datetime
from http import HTTPStatus

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import Sum
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

from recipes.models import (
    FavoriteRecipe, Ingredient, Recipe, ShoppingCart, Subscription, Tag
)


ERROR_NO_SUBSCRIPRION = 'Подписки не было'
ERROR_NO_RECIPE = 'Рецепт не найден'
ERROR_NO_SELF_SUBSCRIPTION = 'Самоподписка не поддерживается'
ERROR_ALREADY_SUBSCRIPTED = 'Подписка уже существует'
ERROR_RECIPE_ALREADY_ADDED = 'Рецепт уже добавлен'

User = get_user_model()


class UserViewSet(DjoserUserViewSet):

    queryset = User.objects.all()

    def get_permissions(self):
        if self.action == 'me':
            return (IsAuthenticated(),)
        return super().get_permissions()

    @action(detail=False,
            methods=('put', 'delete'),
            url_path=settings.SELF_ENDPOINT + '/avatar',
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
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user)
        return Response(serializer.data)

    @action(detail=True,
            methods=('post', 'delete'),
            permission_classes=(IsAuthenticated,),
            )
    def subscribe(self, request, id):
        user = request.user
        author = get_object_or_404(User, id=id)
        if author == user:
            raise ValidationError({'detail': ERROR_NO_SELF_SUBSCRIPTION})
        if request.method == 'DELETE':
            if Subscription.objects.filter(
                user=user,
                author=author,
            ).delete()[0] > 0:
                return Response(status=HTTPStatus.NO_CONTENT)
            raise ValidationError({'detail': ERROR_NO_SUBSCRIPRION})
        if not Subscription.objects.get_or_create(
            user=user,
            author=author
        )[1]:
            raise ValidationError({'detail': ERROR_ALREADY_SUBSCRIPTED})
        return Response(
            SubscriptionSerializer(
                author,
                context={'request': request},
            ).data,
            status=HTTPStatus.CREATED
        )

    @action(detail=False,
            methods=('get',),
            url_path=settings.SUBSCRIPTIONS_ENDPOINT,
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

    def get_permissions(self):
        if self.action == 'create':
            return (IsAuthenticated(),)
        return super().get_permissions()

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
        if not model.objects.get_or_create(
            user=request.user,
            recipe=recipe,
        )[1]:
            raise ValidationError({'detail': ERROR_RECIPE_ALREADY_ADDED})
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
        if not user.carts.exists():
            return Response(status=HTTPStatus.NOT_FOUND)
        current_time = datetime.now()
        return FileResponse(
            generate_shopping_file(
                current_time=current_time,
                ingredients=Ingredient.objects.filter(
                    recipes_ingredients__recipe__carts__user=user
                ).annotate(
                    amount=Sum("recipes_ingredients__amount")
                ).order_by('name').values(),
                recipes=Recipe.objects.filter(
                    carts__user=user
                ).order_by('name').values('name'),
            ),
            as_attachment=True,
            filename=f'to_buy_{current_time.strftime("%Y%m%d")}.txt'
        )

    @action(detail=True,
            methods=('get',),
            url_path='get-link',
            permission_classes=(AllowAny,)
            )
    def get_link(self, request, pk):
        if not Recipe.objects.filter(id=pk).exists():
            raise ValidationError(code=HTTPStatus.NOT_FOUND)
        return Response(
            {'short-link': f'/{settings.SHORT_RECIPE_ENDPOINT}/{pk}'},
            status=HTTPStatus.OK,
        )
