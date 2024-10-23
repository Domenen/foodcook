from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models

from .services import generate_url_slug
from api.constants import (
    MAX_LENGTH_TAGS, MIN_VALUE,
    LENGTH_SHORT_URL, MAX_LENGTH_INGREDIENT,
    MAX_LENGTH_UNIT, MAX_LENGTH_RECIPES,
    MAX_VALUE)
from users.models import User


class Tag(models.Model):
    name = models.CharField(
        'Название',
        max_length=MAX_LENGTH_TAGS,
        unique=True
    )
    slug = models.SlugField(
        'Слаг',
        max_length=MAX_LENGTH_TAGS,
        unique=True
    )

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    name = models.CharField(
        'Название',
        max_length=MAX_LENGTH_INGREDIENT,
        db_index=True
    )
    measurement_unit = models.CharField(
        'Единица измерения',
        max_length=MAX_LENGTH_UNIT,
    )

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        constraints = (
            models.UniqueConstraint(
                fields=('name', 'measurement_unit'),
                name='unique_name_measurement_unit'
            ),
        )

    def __str__(self):
        return self.name


class Recipe(models.Model):
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Автор',
    )
    name = models.CharField(
        'Название',
        max_length=MAX_LENGTH_RECIPES,
    )
    image = models.ImageField(
        'Картинка',
        upload_to='media/recipes/',
    )
    text = models.TextField(
        'Описание',
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient',
        verbose_name='Ингредиенты',
    )
    tags = models.ManyToManyField(
        Tag,
        verbose_name='Теги',
    )
    cooking_time = models.PositiveSmallIntegerField(
        'Время готовки',
        validators=(
            MinValueValidator(
                MIN_VALUE,
                f'Время готовки не может быть меньше {MIN_VALUE}'
            ),
            MaxValueValidator(
                MAX_VALUE,
                f'Время готовки не может быть меньше {MAX_VALUE}'
            )
        )
    )

    slug = models.CharField(
        max_length=LENGTH_SHORT_URL,
        unique=True,
        blank=True,
        null=True,
        verbose_name='Короткая ссылка'
    )

    pub_date = models.DateTimeField(
        'Дата публикации',
        auto_now_add=True,
    )

    class Meta:
        ordering = ('-pub_date',)
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = generate_url_slug(self.__class__, LENGTH_SHORT_URL)
        super().save(*args, **kwargs)


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='recipeingredients',
        verbose_name='Рецепт'

    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='recipeingredients',
        verbose_name='Ингредиент'
    )
    amount = models.PositiveSmallIntegerField(
        'Количество',
        validators=(
            MinValueValidator(
                MIN_VALUE,
                f'Колличество ингридиентов должно быть больше {MIN_VALUE}'
            ),
            MaxValueValidator(
                MAX_VALUE,
                f'Колличество ингридиентов должно быть меньше'
                f'{MAX_VALUE}'
            )
        )
    )

    class Meta:
        verbose_name = 'Ингредиент в рецепте'
        verbose_name_plural = 'Ингредиенты в рецептах'
        constraints = (
            models.UniqueConstraint(
                fields=('recipe', 'ingredient'),
                name='unique_recipe_ingredient'
            ),
        )

    def __str__(self):
        return self.ingredient.name


class UserRecipeModel(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='%(class)ss',
        verbose_name='Пользователь'
    )
    recipe = models.ForeignKey(
        'Recipe',
        on_delete=models.CASCADE,
        related_name='%(class)ss',
        verbose_name='Рецепт'
    )

    class Meta:
        abstract = True

    def __str__(self):
        return (
            f'{self.user.username} добавил {self.recipe.name}'
            f' в {self._meta.verbose_name.lower()}'
        )


class Favorite(UserRecipeModel):
    class Meta(UserRecipeModel.Meta):
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'
        constraints = (
            models.UniqueConstraint(
                fields=('user', 'recipe'),
                name='unique_user_recipe_favorite'
            ),
        )


class ShoppingCart(UserRecipeModel):
    class Meta(UserRecipeModel.Meta):
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Списки покупок'
        constraints = (
            models.UniqueConstraint(
                fields=('user', 'recipe'),
                name='unique_user_recipe_cart'
            ),
        )
