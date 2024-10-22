import datetime

from rest_framework import status
from rest_framework.response import Response


def create_model_recipe(request, instance, serializer):
    serializer = serializer(
        data={'user': request.user.id, 'recipe': instance.id, },
        context={'request': request}
    )
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data, status=status.HTTP_201_CREATED)


def delete_model_recipe(request, model, instance, error_msg):
    deleted_count, _ = model.objects.filter(
        user=request.user, recipe=instance
    ).delete()
    if deleted_count:
        return Response(status=status.HTTP_204_NO_CONTENT)
    return Response(
        {'errors': error_msg},
        status=status.HTTP_400_BAD_REQUEST
    )


def shopping_cart_list(ingredients, cart_recipes):
    today = datetime.datetime.now().strftime('%d-%m-%Y')
    ingredients_info = [
        f'{i}. {ingredient["ingredient_name"].capitalize()}'
        f'({ingredient["ingredient_unit"]}) - '
        f'{ingredient["total_amount"]}'
        for i, ingredient in enumerate(ingredients, start=1)
    ]
    recipe_names = [f' - {recipe.name}' for recipe in cart_recipes]
    shopping_list = '\n'.join([
        f'Дата создания списка: {today}',
        'Рецепты:',
        *recipe_names,
        'Продукты:',
        *ingredients_info
    ])
    return shopping_list
