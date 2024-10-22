import tempfile
from django.db.models import Sum, Count
from django_filters.rest_framework import DjangoFilterBackend
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet
from djoser.serializers import UserCreateSerializer
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .paginations import FoodgramPagination
from .serializers import (AvatarSerializer, FavoriteSerializer,
                          RecipeCreateSerializer, RecipeGetSerializer,
                          ShoppingCartSerializer, IngredientSerializer,
                          TagSerialiser, UserSubscribeRepresentSerializer,
                          UserSubscribeSerializer)
from .services import create_model_recipe, delete_model_recipe
from .filters import IngredientFilter, RecipeFilter
from recipes.models import (Favorite, Ingredient, Recipe,
                            RecipeIngredient, ShoppingCart, Tag)
from users.models import Subscription, User


class FoodgramUserViewSet(UserViewSet):
    pagination_class = FoodgramPagination

    @action(
        methods=('post',),
        detail=False,
        url_name='signup',
    )
    def signup(self, request):
        serializer = UserCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(
        methods=('get',),
        detail=False,
        permission_classes=(IsAuthenticated,),
        url_name='me',
    )
    def me(self, request, *args, **kwargs):
        return super().me(request, *args, **kwargs)

    @action(
        methods=('put',),
        detail=False,
        permission_classes=(IsAuthenticated,),
        url_path='me/avatar',
        url_name='me-avatar',
    )
    def avatar(self, request):
        instance = self.get_instance()
        serializer = AvatarSerializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @avatar.mapping.delete
    def delete_avatar(self, request):
        request.user.avatar = None
        request.user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        methods=('post',),
        detail=True,
        permission_classes=(IsAuthenticated,),
        url_path='subscribe',
        url_name='subscribe',
    )
    def subscribe(self, request, id=None):
        author = get_object_or_404(User, id=id)
        serializer = UserSubscribeSerializer(
            data={'user': request.user.id, 'author': author.id},
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            serializer.data, status=status.HTTP_201_CREATED
        )

    @subscribe.mapping.delete
    def unsubscribe(self, request, id=None):
        author = get_object_or_404(User, id=id)
        deleted_count, _ = Subscription.objects.filter(
            user=request.user, author=author
        ).delete()
        if deleted_count > 0:
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(
            {'errors': 'Вы не подписаны на этого пользователя'},
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(
        methods=('get',),
        detail=False,
        permission_classes=(IsAuthenticated,),
        url_path='subscriptions',
        url_name='subscriptions',
    )
    def subscriptions(self, request):
        queryset = User.objects.filter(
            subscriptions_on_author__user=request.user
        ).annotate(recipes_count=Count('recipes'))
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = UserSubscribeRepresentSerializer(
                page, many=True, context={'request': request}
            )
            return self.get_paginated_response(serializer.data)
        serializer = UserSubscribeRepresentSerializer(
            queryset, many=True, context={'request': request}
        )
        return Response(serializer.data, status=status.HTTP_200_OK)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerialiser
    permission_classes = (AllowAny, )
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (AllowAny, )
    filter_backends = (DjangoFilterBackend, )
    filterset_class = IngredientFilter
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.select_related(
        'author'
    ).prefetch_related('tags', 'ingredients')
    pagination_class = FoodgramPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return RecipeGetSerializer
        return RecipeCreateSerializer

    @action(
        detail=True,
        methods=('get', 'post'),
        permission_classes=(IsAuthenticated,)
    )
    def favorite(self, request, pk):
        recipe = get_object_or_404(Recipe, id=pk)
        if request.method == 'GET':
            in_favorite = Favorite.objects.filter(
                user=request.user, recipe=recipe
            ).exists()
            if in_favorite:
                return Response(
                    {"status": "Рецепт в избранном"},
                    status=status.HTTP_200_OK
                )
            return Response(
                {"status": "Рецепт не в избранном"},
                status=status.HTTP_404_NOT_FOUND
            )
        return create_model_recipe(request, recipe, FavoriteSerializer)

    @favorite.mapping.delete
    def delete_favorite(self, request, pk):
        recipe = get_object_or_404(Recipe, id=pk)
        error_msg = 'Нет этого рецепта в избранном'
        return delete_model_recipe(request, Favorite, recipe, error_msg)

    @action(
        detail=True,
        methods=('get', 'post'),
        permission_classes=(IsAuthenticated,)
    )
    def shopping_cart(self, request, pk):
        recipe = get_object_or_404(Recipe, id=pk)
        if request.method == 'GET':
            in_cart = ShoppingCart.objects.filter(
                user=request.user, recipe=recipe
            ).exists()
            if in_cart:
                return Response(
                    {"status": "Рецепт в списке покупок"},
                    status=status.HTTP_200_OK
                )
            return Response(
                {"status": "Рецепт не в списке покупок"},
                status=status.HTTP_404_NOT_FOUND
            )
        return create_model_recipe(request, recipe, ShoppingCartSerializer)

    @shopping_cart.mapping.delete
    def delete_shopping_cart(self, request, pk):
        recipe = get_object_or_404(Recipe, id=pk)
        error_msg = 'Нет этого рецепта в списке покупок'
        return delete_model_recipe(request, ShoppingCart, recipe, error_msg)

    @action(
        detail=False,
        methods=('get',),
        permission_classes=(IsAuthenticated,)
    )
    def download_shopping_cart(self, request):
        ingredients = RecipeIngredient.objects.filter(
            recipe__shoppingcarts__user=request.user
        ).values(
            'ingredient__name', 'ingredient__measurement_unit'
        ).annotate(ingredient_amount=Sum('amount'))
        shopping_list = self.generate_shopping_list(ingredients)
        with tempfile.NamedTemporaryFile(
            mode='w+', delete=False
        ) as temp_file:
            temp_file.write(shopping_list)
            temp_file.seek(0)
            response = FileResponse(temp_file, content_type='text/plain')
            response['Content-Disposition'] = (
                'attachment; filename="shopping_cart.txt"'
            )
            return response

    @staticmethod
    def generate_shopping_list(ingredients):
        shopping_list = ['Список покупок:\n']
        for ingredient in ingredients:
            name = ingredient['ingredient__name']
            unit = ingredient['ingredient__measurement_unit']
            amount = ingredient['ingredient_amount']
            shopping_list.append(f'\n{name} - {amount}, {unit}')
        return "\n".join(shopping_list)

    @action(
        detail=True,
        methods=('get',),
        permission_classes=(AllowAny,),
        url_path='get-link'
    )
    def get_link(self, request, pk):
        recipe = get_object_or_404(Recipe, id=pk)
        link = request.build_absolute_uri(f'/s/{recipe.url_slug}')
        return Response({"short-link": link})
