from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (CartAPIView, DownloadCartVAPIView, FavoriteAPIView,
                    IngredientViewSet, RecipeViewSet, SubscribeCreateAPIView,
                    SubscribeListAPIView, TagViewSet)

app_name = 'api'
router = DefaultRouter()

router.register('ingredients', IngredientViewSet, basename='ingredients')
router.register('tags', TagViewSet, basename='tags')
router.register('recipes', RecipeViewSet, basename='recipes')


urlpatterns = [
    path('', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
    path(
        'recipes/<int:id>/shopping_cart/',
        CartAPIView.as_view(),
        name='cart'
    ),
    path(
        'recipes/<int:id>/favorite/',
        FavoriteAPIView.as_view(),
        name='favorite'
    ),
    path(
        'users/<int:id>/subscribe/',
        SubscribeCreateAPIView.as_view(),
        name='subscribe'
    ),
    path(
        'users/subscriptions/',
        SubscribeListAPIView.as_view(),
        name='subscriptions'
    ),
    path(
        'recipes/download_shopping_cart/',
        DownloadCartVAPIView.as_view(),
        name='download_cart'
    ),
    path('', include(router.urls)),
]