from django.shortcuts import get_object_or_404, redirect

from .models import Recipe


def redirect_to_recipe(request, slug):
    recipe = get_object_or_404(Recipe, slug=slug)
    return redirect(f'/recipes/{recipe.id}')
