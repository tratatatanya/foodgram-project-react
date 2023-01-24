from django.db.models import Sum
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from recipes.models import (Cart, Favorite, Ingredient, IngredientInRecipe,
                            Recipe, Tag)
from users.models import Subscribe, User

from .filters import IngredientFilter, RecipeFilter
from .permissions import IsAuthorOrReadOnly, ReadOnly
from .serializers import (CartSerializer, FavoriteSerializer,
                          IngredientSerializer, RecipeCreateSerializer,
                          RecipeSerializer, SubscribeCreateSerializer,
                          SubscriptionSerializer, TagSerializer)


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
        user_id = request.user.id
        data = {"user": user_id, "recipe": id}
        serializer = FavoriteSerializer(
            data=data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request, id):
        user = request.user
        recipe = get_object_or_404(Recipe, id=id)
        deleting_obj = Favorite.objects.all().filter(user=user, recipe=recipe)
        if not deleting_obj:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        deleting_obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class CartAPIView(APIView):

    def post(self, request, id):
        user_id = request.user.id
        data = {'user': user_id, 'recipe': id}
        serializer = CartSerializer(data=data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request, id):
        user = request.user
        recipe = get_object_or_404(Recipe, id=id)
        deleting_obj = Cart.objects.all().filter(user=user, recipe=recipe)
        if not deleting_obj:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        deleting_obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class DownloadCartVAPIView(APIView):
    def get(self, request):
        ingredients = (
            Cart.objects.annotate(
                result=Sum("recipe__ingredients__ingredient__amount"),
            )
            .values(
                "recipe__ingredients__name",
                "recipe__ingredients__measurement_unit",
                "result",
            ).filter(user=request.user)
        )
        ingredients_dict = {
            i["recipe__ingredients__name"]: i for i in ingredients
        }.values()
        with open("Ingredients_in_cart.txt", "w", encoding="utf-8") as f:
            for key in ingredients_dict:
                f.write(
                    (
                        f'{key["recipe__ingredients__name"]} - {key["result"]}'
                        f'{key["recipe__ingredients__measurement_unit"]} \n'
                    )
                )
        file = "./Ingredients_in_cart.txt"
        return FileResponse(open(file, 'rb'), as_attachment=True,
                            filename='Ingredients_in_cart.txt')


class SubscribeListAPIView(APIView):
    queryset = Subscribe.objects.all()
    serializer_class = SubscriptionSerializer

    def get_queryset(self):
        user = self.request.user
        new_queryset = User.objects.all().filter(following_author__user=user)
        return new_queryset


class SubscribeCreateAPIView(APIView):

    def post(self, request, id):
        data = {'user': request.user.id, 'author': id}
        serializer = SubscribeCreateSerializer(
            data=data, context={'request': request}
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
        if not deleting_obj:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        deleting_obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
