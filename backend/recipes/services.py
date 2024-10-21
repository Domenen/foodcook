from django.shortcuts import get_object_or_404, redirect

from .models import Recipe


def redirect_to_recipe(request, url_slug):
    recipe = get_object_or_404(Recipe, url_slug=url_slug)
    return redirect(f'/recipes/{recipe.id}')
