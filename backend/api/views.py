import base64
import hashlib
from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import (
    AllowAny, IsAuthenticated,
)
from rest_framework.response import Response

from .filters import IngredientFilter, RecipeFilter
from .permissions import IsAuthorIsAdminOrReadOnly
from .serializers import (
    ChangePasswordSerializer,
    FavoriteRecipeSerializer,
    IngredientSerializer,
    RecipeSerializer,
    ShoppingCartSerializer,
    SubscriptionSerializer,
    TagSerializer,
    UserAvatarSerializer,
    UserShowSerializer,
    UserCreateSerializer,
)
from foodgram_backend.settings import (
    FRONTEND_RECIPE_ENDPOINT,
    SELF_ENDPOINT, SUBSCRIPTIONS_ENDPOINT, SHORT_RECIPE_ENDPOINT
)
from recipes.models import (
    FavoriteRecipe, Ingredient, Recipe, RecipeLinkShortener, ShoppingCart, Tag
)
from users.models import Subscription


ERROR_WRONG_PASSWORD = 'Вы ввели неверный пароль'
ERROR_NO_SUBSCRIPRION = 'Подписки не было'
ERROR_NO_RECIPE = 'Рецепт не найден'


User = get_user_model()


class UserViewSet(viewsets.ModelViewSet):

    queryset = User.objects.all().prefetch_related()
    search_fields = ('username', 'email',)
    filterset_fields = ('username', 'email',)
    permission_classes = (AllowAny,)
    http_method_names = ('delete', 'get', 'post', 'put',)

    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        return UserShowSerializer

    @action(detail=False,
            methods=('post',),
            url_path='set_password',
            permission_classes=(IsAuthenticated,)
            )
    def ser_password(self, request):
        user = request.user
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if user.check_password(request.data['current_password']):
            user.password = serializer.validated_data['new_password']
            user.save()
            return Response(status=HTTPStatus.NO_CONTENT)
        return Response(
            {'current_password': ERROR_WRONG_PASSWORD},
            status=HTTPStatus.BAD_REQUEST
        )

    @action(detail=False,
            methods=('get',),
            url_path=SELF_ENDPOINT,
            permission_classes=(IsAuthenticated,)
            )
    def self_endpoint(self, request):
        serializer = UserShowSerializer(
            request.user,
            data=request.data,
            context={"request": request},
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save(
            role=request.user.role
        )
        return Response(serializer.data, status=HTTPStatus.OK)

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
            context={"request": request},
        )
        if serializer.is_valid(raise_exception=True):
            serializer.save(user=request.user)
            return Response(serializer.data)

    @action(detail=True,
            methods=('post', 'delete'),
            permission_classes=(IsAuthenticated,),
            )
    def subscribe(self, request, pk):
        subscribed_to = get_object_or_404(User, id=pk)
        if request.method == 'DELETE':
            if Subscription.objects.filter(
                user=request.user,
                subscribed_to=subscribed_to,
            ).delete()[0] > 0:
                return Response(status=HTTPStatus.NO_CONTENT)
            else:
                return Response(
                    {'detail': ERROR_NO_SUBSCRIPRION},
                    status=HTTPStatus.BAD_REQUEST
                )
        serializer = SubscriptionSerializer(
            data={
                "user": self.request.user.username,
                "subscribed_to": subscribed_to.username,
            },
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user)
        return Response(serializer.data, status=HTTPStatus.CREATED)

    @action(detail=False,
            methods=('get',),
            url_path=SUBSCRIPTIONS_ENDPOINT,
            permission_classes=(IsAuthenticated,),
            )
    def subscriptions(self, request):
        return self.get_paginated_response(
            SubscriptionSerializer(
                self.paginate_queryset(
                    Subscription.objects.filter(user=request.user),
                ),
                many=True,
                context={"request": request},
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
    permission_classes = (IsAuthorIsAdminOrReadOnly,)
    filterset_class = RecipeFilter

    def modify_recipe_connection(self, request, pk, model, serializer_type):
        recipe = get_object_or_404(Recipe, id=pk)
        if request.method == 'DELETE':
            if model.objects.filter(
                user=request.user,
                recipe=recipe,
            ).delete()[0] > 0:
                return Response(status=HTTPStatus.NO_CONTENT)
            else:
                return Response(
                    {'detail': ERROR_NO_RECIPE},
                    status=HTTPStatus.BAD_REQUEST
                )
        serializer = serializer_type(
            data={
                "user": self.request.user.id,
                "recipe": recipe.id,
            },
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=HTTPStatus.CREATED)

    @action(detail=True,
            methods=('post', 'delete'),
            permission_classes=(IsAuthenticated,),
            )
    def favorite(self, request, pk):
        return self.modify_recipe_connection(
            pk=pk,
            request=request,
            model=FavoriteRecipe,
            serializer_type=FavoriteRecipeSerializer,
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
            serializer_type=ShoppingCartSerializer,
        )

    @action(detail=False,
            methods=('get',),
            permission_classes=(IsAuthenticated,),
            )
    def download_shopping_cart(self, request):
        user = request.user
        if not user.cart.exists():
            return Response(status=HTTPStatus.NOT_FOUND)
        file_name = 'to_buy.txt'
        lines = []
        values = Ingredient.objects.filter(
            in_recipes__recipe__in_carts__user=user
        ).annotate(
            amount=Sum("in_recipes__amount")
        ).order_by('name').values()
        for value in values:
            lines.append(
                '{0}: {1} {2}'.format(
                    value['name'],
                    value['amount'],
                    value['measurement_unit']
                )
            )
        file_response = HttpResponse(
            content='\n'.join(lines), content_type="text/plain,charset=utf8"
        )
        file_response['Content-Disposition'] = (
            f'attachment; filename={file_name}'
        )
        return file_response

    @action(detail=True,
            methods=('get',),
            url_path='get-link',
            permission_classes=(AllowAny,)
            )
    def get_link(self, request, pk):
        created = False
        recipe = get_object_or_404(Recipe, id=pk)
        if RecipeLinkShortener.objects.filter(recipe=recipe).exists():
            short_url = RecipeLinkShortener.objects.get(
                recipe=recipe
            ).short_url
            created = True
        length = 1
        while not created:
            short_url = base64.urlsafe_b64encode(
                hashlib.shake_256(bytes(pk, 'utf-8')).digest(length)
            ).decode('ascii')
            length += 1
            if not RecipeLinkShortener.objects.filter(
                short_url=short_url
            ).exists():
                RecipeLinkShortener.objects.create(
                    recipe=recipe,
                    short_url=short_url
                )
                created = True
        short_url = request.build_absolute_uri(
            f'/{SHORT_RECIPE_ENDPOINT}/{short_url}'
        )
        return Response({'short-link': short_url}, status=HTTPStatus.OK)


def redirect_from_recipe_short_url(request, short_url):
    recipe_link = get_object_or_404(
        RecipeLinkShortener,
        short_url=short_url,
    )
    return redirect(
        request.build_absolute_uri(
            f'/{FRONTEND_RECIPE_ENDPOINT}/{recipe_link.id}/'
        )
    )
