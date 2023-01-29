from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from recipes.models import (Cart, Favorite, Ingredient, IngredientInRecipe,
                            Recipe, Tag)
from users.models import Subscribe, User
from .filters import IngredientFilter, RecipeFilter
from .permissions import IsAuthorOrReadOnly, ReadOnly
from .serializers import (CartSerializer,  FavoriteSerializer,
                          IngredientSerializer, RecipeCreateSerializer,
                          RecipeSerializer, SubscribeCreateSerializer,
                          SubscriptionSerializer, TagSerializer,)
from .utils import custom_delete, custom_post


class IngredientViewSet(ModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (IsAuthenticatedOrReadOnly,)
    pagination_class = None
    filter_backends = [DjangoFilterBackend]
    filterset_class = IngredientFilter


class TagViewSet(ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None
    permission_classes = (ReadOnly,)


class RecipeViewSet(ModelViewSet):
    queryset = Recipe.objects.all()
    permission_classes = (IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly)
    filter_backends = [DjangoFilterBackend]
    filterset_class = RecipeFilter


    def get_serializer_class(self):
        if self.request.method in ['POST', 'PATCH']:
            return RecipeCreateSerializer
        return RecipeSerializer


class FavoriteAPIView(APIView):

    def post(self, request, id):
        return custom_post(request, id, FavoriteSerializer)

    def delete(self, request, id):
        return custom_delete(request, id, Favorite)


class CartAPIView(APIView):
    pagination_class = PageNumberPagination

    def get(self, request):
        return Cart.objects.filter(user=request.user)

    def post(self, request, id):
        return custom_post(request, id, CartSerializer)

    def delete(self, request, id):
        return custom_delete(request, id, Cart)


class DownloadCartVAPIView(APIView):
    def get(self, request):
        user = request.user
        if not user.shopping_cart.exists():
            return Response(
                'Корзина пуста', status=status.HTTP_400_BAD_REQUEST
            )
        ingredient_name = "recipe__ingredients__name"
        ingredient_measurement_unit = "recipe__ingredients__measurement_unit"
        ingredient_amount = "recipe__ingredients__ingredient__amount"
        ingredients = (
            Cart.objects.annotate(
                result=Sum(ingredient_amount),
            )
            .values(
                ingredient_name,
                ingredient_measurement_unit,
                "result",
            ).filter(user=request.user)
        )
        cart = {
            x["recipe__ingredients__name"]: x for x in ingredients
        }.values()
        text = []
        for item in cart:
            new_row = (
                f'{item[ingredient_name]} - {item["result"]}'
                f'{item[ingredient_measurement_unit]}\n'
            )
            if new_row not in text:
                text += new_row
            else:
                continue
        response = HttpResponse(text, content_type='text/plain')
        filename = 'Ingredients_in_cart.txt'
        response['Content-Disposition'] = f'attachment; filename={filename}'
        return response


class SubscribeListViewSet(ModelViewSet):
    queryset = Subscribe.objects.all()
    serializer_class = SubscriptionSerializer

    def get_queryset(self):
        user = self.request.user
        return User.objects.filter(following_author__user=user)


class SubscribeCreateAPIView(APIView):

    def post(self, request, id):
        user = request.user
        serializer = SubscribeCreateSerializer(
            data={"user": user.id, "author": id},
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request, id):
        user = request.user
        author = get_object_or_404(User, id=id)
        deleting_obj = Subscribe.objects.filter(
            user=user, author=author
        )
        if deleting_obj.exists():
            deleting_obj.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_400_BAD_REQUEST)
