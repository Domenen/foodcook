from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (IngredientViewSet, RecipeViewSet, TagViewSet,
                    UserSubscribeView, UserSubscriptionsViewSet,
                    redirect_to_recipe, CustomUserViewSet)


router = DefaultRouter()
router.register(r"users", CustomUserViewSet, basename="me")
router.register(r'tags', TagViewSet, basename='tags')
router.register(r'ingredients', IngredientViewSet, basename='ingredients')
router.register(r'recipes', RecipeViewSet, basename='recipes')


urlpatterns = [
    path("auth/", include("djoser.urls.authtoken")),
    path("users/subscriptions/",
         UserSubscriptionsViewSet.as_view({"get": "list"})),
    path("users/<int:user_id>/subscribe/", UserSubscribeView.as_view()),
    path("s/<short_url>", redirect_to_recipe, name='redirect_full_url'),
    path("", include(router.urls)),
]
