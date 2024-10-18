from django.db.models import Sum
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import HttpResponse, get_object_or_404, redirect
from djoser.views import UserViewSet
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .permissions import IsAdminAuthorOrReadOnly
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
        methods=('get'),
        detail=False,
        permission_classes=(IsAuthenticated, ),
        url_name='me',
    )
    def me(self, request, *args, **kwargs):
        return super().me(request, *args, **kwargs)

    @action(
        methods=('put'),
        detail=False,
        permission_classes=(IsAuthenticated, ),
        url_path='me/avatar',
        url_name='me-avatar',
    )
    def avatar(self, request):
        serializer = self._change_avatar(request.data)
        return Response(serializer.data)

    @avatar.mapping.delete
    def delete_avatar(self, request):
        data = request.data
        if 'avatar' not in data:
            data = {'avatar': None}
        self._change_avatar(data)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def _change_avatar(self, data):
        instance = self.get_instance()
        serializer = AvatarSerializer(instance, data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return serializer


class UserSubscribeView(APIView):
    pagination_class = FoodgramPagination

    def post(self, request, user_id):
        author = get_object_or_404(User, id=user_id)
        serializer = UserSubscribeSerializer(
            data={'user': request.user.id, 'author': author.id},
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request, user_id):
        author = get_object_or_404(User, id=user_id)
        if not Subscription.objects.filter(
            user=request.user,
            author=author
        ).exists():
            return Response(
                {'errors': 'Вы не подписаны на этого пользователя'},
                status=status.HTTP_400_BAD_REQUEST
            )
        Subscription.objects.get(
            user=request.user.id,
            author=user_id
        ).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class UserSubscriptionsViewSet(mixins.ListModelMixin,
                               viewsets.GenericViewSet):
    permission_classes = (IsAdminAuthorOrReadOnly,)
    serializer_class = UserSubscribeRepresentSerializer
    pagination_class = FoodgramPagination

    def get_queryset(self):
        return User.objects.filter(
            subscriptions_on_author__user=self.request.user
        )


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
    queryset = Recipe.objects.all()
    pagination_class = FoodgramPagination
    permission_classes = (IsAdminAuthorOrReadOnly, )
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    http_method_names = ('get', 'post', 'patch', 'delete')

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return RecipeGetSerializer
        return RecipeCreateSerializer

    @action(
        detail=True,
        methods=('post', 'delete'),
        permission_classes=(IsAuthenticated, )
    )
    def favorite(self, request, pk):
        recipe = get_object_or_404(Recipe, id=pk)
        if request.method == 'POST':
            return create_model_recipe(request, recipe, FavoriteSerializer)

        if request.method == 'DELETE':
            error_msg = 'Нет этого рецепта в избранном'
            return delete_model_recipe(
                request, Favorite,
                recipe, error_msg
            )
        return None

    @action(
        detail=True,
        methods=('post', 'delete'),
        permission_classes=(IsAuthenticated, )
    )
    def shopping_cart(self, request, pk):
        recipe = get_object_or_404(Recipe, id=pk)
        if request.method == 'POST':
            return create_model_recipe(
                request, recipe,
                ShoppingCartSerializer
            )

        if request.method == 'DELETE':
            error_msg = 'Нет этого рецепта в списке покупок'
            return delete_model_recipe(
                request, ShoppingCart,
                recipe, error_msg
            )
        return None

    @action(
        detail=False,
        methods=('get'),
        permission_classes=(AllowAny, )
    )
    def download_shopping_cart(self, request):
        ingredients = RecipeIngredient.objects.filter(
            recipe__carts__user=request.user
        ).values(
            'ingredient__name', 'ingredient__measurement_unit'
        ).annotate(ingredient_amount=Sum('amount'))
        shopping_list = ['Список покупок:\n']
        for ingredient in ingredients:
            name = ingredient['ingredient__name']
            unit = ingredient['ingredient__measurement_unit']
            amount = ingredient['ingredient_amount']
            shopping_list.append(f'\n{name} - {amount}, {unit}')
        response = HttpResponse(shopping_list, content_type='text/plain')
        response['Content-Disposition'] = (
            'attachment; filename="shopping_cart.txt"'
        )
        return response

    def _post_author_recipe(self, request, pk):
        serializer = self.get_serializer(data=dict(recipe=pk))
        serializer.is_valid(raise_exception=True)
        serializer.save(author=self.request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def _delete_author_recipe(self, request, pk, model):
        recipe = get_object_or_404(Recipe, pk=pk)
        obj_count, _ = model.objects.filter(
            author=self.request.user,
            recipe=recipe,
        ).delete()

        if obj_count == 0:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        return Response(status=status.HTTP_204_NO_CONTENT)


class GetLinkViewSet(APIView):
    queryset = Recipe.objects.all()
    permission_classes = (AllowAny,)
    http_method_names = ('get')

    @action(
        detail=False, methods=("GET"),
        permission_classes=(AllowAny, )
    )
    def get(self, request, pk):
        recipe = get_object_or_404(Recipe, id=pk)
        link = request.build_absolute_uri()
        link_str = link.replace(
            f'/api/recipes/{pk}/get-link/',
            f'/s/{recipe.url_slug}'
        )
        data = {"short-link": link_str}
        return Response(data)


def redirect_to_recipe(request, url_slug):
    recipe = get_object_or_404(Recipe, url_slug=url_slug)
    return redirect(f'/recipes/{recipe.id}')
