from django.shortcuts import get_object_or_404, redirect
from django.utils.crypto import get_random_string


def redirect_to_recipe(request, url_slug):
    from .models import Recipe
    recipe = get_object_or_404(Recipe, url_slug=url_slug)
    return redirect(f'/recipes/{recipe.id}')


def generate_url_slug(model_class, length):
    while True:
        url_slug = get_random_string(length=length)
        if not model_class.objects.filter(url_slug=url_slug).exists():
            return url_slug
