from django.contrib import admin

from .models import (Favorite, Ingredient, Recipe,
                     RecipeIngredient, ShoppingCart, Tag)

MIN_INGREDIENT = 1
EXTRA = 1


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('pk', 'name', 'slug')
    list_display_links = ('pk', 'name', 'slug')


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('pk', 'name', 'measurement_unit')
    search_fields = ('name',)
    list_filter = ('name',)


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = EXTRA
    min_num = MIN_INGREDIENT


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('pk', 'name', 'author', 'favorites_amount')
    search_fields = ('name', 'author')
    list_filter = ('name', 'author', 'tags')
    inlines = [
        RecipeIngredientInline,
    ]

    def favorites_amount(self, obj):
        return obj.favorites.count()


@admin.register(RecipeIngredient)
class RecipeIngredientAdmin(admin.ModelAdmin):
    list_display = ('pk', 'recipe', 'ingredient', 'amount')


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('pk', 'user', 'recipe')
    search_fields = ('user', 'recipe')


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ('pk', 'user', 'recipe')
    search_fields = ('user', 'recipe')
