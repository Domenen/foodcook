from django.db import transaction
from django.forms import ValidationError
from djoser.serializers import UserSerializer
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator
from drf_extra_fields.fields import Base64ImageField

from recipes.models import (Favorite, Ingredient,
                            Recipe, RecipeIngredient,
                            ShoppingCart, Tag)
from users.models import User, Subscription
from .constants import (
    MIN_VALUE, MAX_VALUE
)


class UserGetSerializer(UserSerializer):
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id', 'email', 'username', 'first_name', 'last_name',
            'is_subscribed', 'avatar'
        )

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        return (
            request
            and request.user.is_authenticated
            and obj.subscriptions_on_author.filter(
                user=request.user
            ).exists()
        )


class AvatarSerializer(serializers.ModelSerializer):
    avatar = Base64ImageField(allow_null=True)

    class Meta:
        model = User
        fields = ('avatar',)


class RecipeSmallSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class UserSubscribeRepresentSerializer(UserGetSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.IntegerField(read_only=True, default=0)

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + (
            'first_name', 'last_name',
            'is_subscribed', 'avatar',
            'recipes', 'recipes_count',
        )
        read_only_fields = (
            'email', 'username',
            'first_name', 'last_name',
            'is_subscribed', 'recipes',
            'recipes_count', 'avatar'
        )

    def get_recipes(self, obj):
        request = self.context['request']
        recipes_limit = request.query_params.get('recipes_limit')
        recipes = obj.recipes.all()
        if recipes_limit:
            try:
                recipes = recipes[:int(recipes_limit)]
            except (ValueError, TypeError):
                pass
        return RecipeSmallSerializer(
            recipes, many=True,
            context=self.context
        ).data


class UserSubscribeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscription
        fields = '__all__'
        validators = (
            UniqueTogetherValidator(
                queryset=Subscription.objects.all(),
                fields=('user', 'author'),
                message='Уже подписаны на этого пользователя'
            ),
        )

    def validate(self, data):
        request = self.context.get('request')
        if request.user == data['author']:
            raise serializers.ValidationError(
                'Нельзя подписаться на себя'
            )
        return data

    def to_representation(self, instance):
        return UserSubscribeRepresentSerializer(
            instance.author, context=self.context
        ).data


class TagSerialiser(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class IngredientGetSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(
        source='ingredient.id', read_only=True
    )
    name = serializers.CharField(
        source='ingredient.name', read_only=True
    )
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit',

    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class IngredientPostSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all()
    )
    amount = serializers.IntegerField(
        max_value=MAX_VALUE,
        min_value=MIN_VALUE
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount')


class RecipeGetSerializer(serializers.ModelSerializer):
    tags = TagSerialiser(many=True, read_only=True)
    author = UserGetSerializer(read_only=True)
    ingredients = IngredientGetSerializer(
        many=True, read_only=True,
        source='recipeingredients'
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    image = Base64ImageField(required=False)

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'author', 'ingredients',
            'is_favorited', 'is_in_shopping_cart', 'name',
            'image', 'text', 'cooking_time'
        )

    def get_is_favorited(self, obj):
        request = self.context['request']
        return (
            request
            and request.user.is_authenticated
            and obj.favorites.filter(
                user=request.user
            ).exists()
        )

    def get_is_in_shopping_cart(self, obj):
        request = self.context['request']
        return (
            request
            and request.user.is_authenticated
            and obj.shoppingcarts.filter(
                user=request.user
            ).exists()
        )


class RecipeCreateSerializer(serializers.ModelSerializer):
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), many=True
    )
    ingredients = IngredientPostSerializer(many=True)
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            'ingredients', 'tags',
            'image', 'name',
            'text', 'cooking_time',
        )

    def validate_image(self, image_data):
        if not image_data:
            raise serializers.ValidationError(
                'Нужно изображение блюда'
            )
        return image_data

    def validate(self, data):
        tags = data.get('tags', [])
        if not tags:
            raise serializers.ValidationError(
                {'tags': 'Нужен тэг'}
            )

        if len(set(tags)) != len(tags):
            raise serializers.ValidationError(
                {'tags': 'Нужен уникальный тэг'}
            )

        ingredients = data.get('ingredients', [])
        if not ingredients:
            raise serializers.ValidationError(
                {'ingredients': 'Нужен минимум 1 ингридиент'}
            )

        id_ingredients = {
            ingredient['id'] for ingredient in ingredients
        }
        if len(ingredients) != len(id_ingredients):
            raise serializers.ValidationError(
                {'ingredients': 'Ингредиенты должны быть уникальными'}
            )
        return data

    def create(self, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        with transaction.atomic():
            recipe = Recipe.objects.create(
                author=self.context['request'].user, **validated_data
            )
            recipe.tags.set(tags)
            self.add_ingredients_to_recipe(recipe, ingredients)
            return recipe

    def update(self, instance, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        with transaction.atomic():
            instance.ingredients.clear()
            instance.tags.set(tags)
            self.add_ingredients_to_recipe(instance, ingredients)
            return instance or super().update(instance, validated_data)

    @staticmethod
    def add_ingredients_to_recipe(recipe, ingredients):
        RecipeIngredient.objects.bulk_create(
            RecipeIngredient(
                recipe=recipe,
                ingredient=ingredient['id'],
                amount=ingredient['amount'],
            )
            for ingredient in ingredients
        )

    def to_representation(self, instance):
        return RecipeGetSerializer(instance, context=self.context).data


class FavoriteAndShoppingCartSerializer(serializers.ModelSerializer):

    model_name = ''

    def validate(self, data):
        user = self.context['request'].user
        recipe = data.get('recipe')
        model = self.Meta.model

        if model.objects.filter(user=user, recipe=recipe).exists():
            raise ValidationError(
                f'Рецепт уже есть в {model._meta.verbose_name}'
                f' ({self.model_name})'
            )
        return data

    def to_representation(self, instance):
        return RecipeSmallSerializer(
            instance.recipe,
            context=self.context
        ).data


class FavoriteSerializer(FavoriteAndShoppingCartSerializer):
    model_name = 'избранное'

    class Meta:
        model = Favorite
        fields = '__all__'


class ShoppingCartSerializer(FavoriteAndShoppingCartSerializer):
    model_name = 'список покупок'

    class Meta:
        model = ShoppingCart
        fields = '__all__'
