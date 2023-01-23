from django.urls import include, path, re_path
from djoser import views
from rest_framework.routers import DefaultRouter

from .views import (IngredientViewSet, TagViewSet, RecipeViewSet,
                    CartAPIView, FavoriteAPIView, SubscribeAPIView,
                    SubscriptionAPIView, DownloadCartVAPIView)


app_name = 'api'
router = DefaultRouter()

router.register('ingredients', IngredientViewSet, basename='ingredients')
router.register('tags', TagViewSet, basename='tags')
router.register('recipes', RecipeViewSet, basename='recipes')


urlpatterns = [
    path('', include('djoser.urls')),
    path("auth/token/login/", views.TokenCreateView.as_view(), name="login"),
    path(
        "auth/token/logout/", views.TokenDestroyView.as_view(), name="logout"
    ),
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
        SubscribeAPIView.as_view(),
        name='subscribe'
    ),
    path(
        'users/subscriptions/',
        SubscriptionAPIView.as_view(),
        name='subscriptions'
    ),
    path(
        'recipes/download_shopping_cart/',
        DownloadCartVAPIView.as_view(),
        name='download_cart'
    ),
    path('', include(router.urls)),
    # re_path(r'^auth/', include('djoser.urls.authtoken')),
]