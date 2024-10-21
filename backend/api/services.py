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
    deleted_count, _ = model.objects.filter(user=request.user, recipe=instance).delete()
    if deleted_count > 0:
        return Response(status=status.HTTP_204_NO_CONTENT)
    return Response({'errors': error_msg}, status=status.HTTP_400_BAD_REQUEST)
