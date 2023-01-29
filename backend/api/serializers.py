from django.shortcuts import get_object_or_404
from djoser.serializers import UserCreateSerializer, UserSerializer
from drf_extra_fields.fields import Base64ImageField
from rest_framework.serializers import (IntegerField, ModelSerializer,
                                        PrimaryKeyRelatedField, ReadOnlyField,
                                        SerializerMethodField)
from rest_framework.validators import UniqueTogetherValidator, ValidationError

from recipes.models import (Cart, Favorite, Ingredient, IngredientInRecipe,
                            Recipe, Tag, TagInRecipe)
from users.models import Subscribe, User


class CustomUserSerializer(UserSerializer):
    is_subscribed = SerializerMethodField()

    class Meta:
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed'
        )
        model = User

    def get_is_subscribed(self, instance):
        user = self.context.get('request').user
        if user.is_anonymous or instance.username == user:
            return False
        return Subscribe.objects.filter(user=user, author=instance).exists()


class SignUpSerializer(UserCreateSerializer):
    """Сериализация регистрации пользователя."""

    class Meta:
        model = User
        fields = (
            'username',
            'password',
            'first_name',
            'last_name',
            'email',
        )


class TagSerializer(ModelSerializer):

    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug')


class IngredientSerializer(ModelSerializer):

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class IngredientInRecipeSerializer(ModelSerializer):
    id = ReadOnlyField(source="ingredient.id")
    name = ReadOnlyField(source="ingredient.name")
    measurement_unit = ReadOnlyField(source="ingredient.measurement_unit")

    class Meta:
        model = IngredientInRecipe
        fields = (
            "id",
            "name",
            "measurement_unit",
            "amount",
        )


class RecipeSerializer(ModelSerializer):
    tags = TagSerializer(many=True)
    author = CustomUserSerializer(read_only=True)
    image = Base64ImageField()
    is_favorited = SerializerMethodField()
    is_in_shopping_cart = SerializerMethodField()
    ingredients = IngredientInRecipeSerializer(
        many=True,
        required=True,
        source='recipe'
    )

    class Meta:
        model = Recipe
        fields = (
            'id', 'name', 'text', 'image', 'cooking_time', 'text', 'author',
            'ingredients', 'is_favorited', 'is_in_shopping_cart', 'tags'
        )

    def get_is_favorited(self, instance):
        if self.context['request'].user.is_anonymous:
            return False
        user_id = self.context['request'].user.id
        favorite = Favorite.objects.filter(user=user_id, recipe=instance)
        return favorite.exists()

    def get_is_in_shopping_cart(self, instance):
        if self.context['request'].user.is_anonymous:
            return False
        user_id = self.context['request'].user.id
        recipe_in_cart = Cart.objects.filter(user=user_id, recipe=instance)
        return recipe_in_cart.exists()


class IngredientInRecipeCreateSerializer(ModelSerializer):
    id = PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(),
        source='ingredient'
    )
    amount = IntegerField()

    class Meta:
        model = IngredientInRecipe
        fields = ('id', 'amount',)


class RecipeCreateSerializer(ModelSerializer):
    tags = PrimaryKeyRelatedField(many=True, queryset=Tag.objects.all())
    ingredients = IngredientInRecipeCreateSerializer(many=True)
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'ingredients',
            'name',
            'image',
            'text',
            'cooking_time',
        )

    def add_ingredients(self, ingredients, recipe):
        for ingredient in ingredients:
            IngredientInRecipe.objects.update_or_create(
                recipe=recipe,
                ingredient=ingredient['ingredient'],
                amount=ingredient['amount']
            )

    def create(self, validated_data):
        author = self.context['request'].user
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(author=author, **validated_data)
        self.add_ingredients(ingredients, recipe)
        recipe.tags.set(tags)
        return recipe

    def update(self, recipe, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        super().update(recipe, validated_data)
        recipe.ingredients.clear()
        self.add_ingredients(ingredients, recipe)
        recipe.tags.set(tags) if tags else None
        return recipe

    def validate(self, data):
        ingredients = data.get("ingredients")
        if not ingredients:
            raise ValidationError(
                {"Ошибка": "Необходимо выбрать хотя бы один ингредиент"}
            )
        for ingredient in ingredients:
            if ingredients.count(ingredient) > 1:
                id = ingredient["id"]
                name = Ingredient.objects.all().get(id=id).name
                raise ValidationError({f"{name}": f"{name} уже есть в списке"})
        return data

    def to_representation(self, recipe):
        return RecipeSerializer(
            recipe, context={'request': self.context.get('request')}
        ).data


class RecipeInFavoriteSerializer(ModelSerializer):

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class FavoriteSerializer(ModelSerializer):

    class Meta:
        model = Favorite
        fields = ('user', 'recipe')

    def validate(self, data):
        user = self.context.get('request').user
        recipe = self.context.get('recipe_id')
        if Favorite.objects.filter(user=user,
                                   recipe=recipe).exists():
            raise ValidationError('Рецепт уже в избранном')
        return data

    def to_representation(self, instance):
        return RecipeInFavoriteSerializer(instance.recipe).data


class CartSerializer(ModelSerializer):

    class Meta:
        model = Cart
        fields = ('user', 'recipe')

    def validate(self, data):
        user = self.context.get('request').user
        recipe = self.context.get('recipe_id')
        if Cart.objects.filter(user=user,
                               recipe=recipe).exists():
            raise ValidationError('Рецепт уже добавлен в корзину')
        return data

    def to_representation(self, instance):
        request = self.context.get('request')
        context = {'request': request}
        return RecipeInFavoriteSerializer(instance.recipe, context=context).data


class RecipeInSubscriptionsSerializer(ModelSerializer):

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class SubscriptionSerializer(ModelSerializer):
    recipes = SerializerMethodField()
    recipes_count = SerializerMethodField()
    is_subscribed = SerializerMethodField()

    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name',
                  'last_name', 'recipes', 'is_subscribed', 'recipes_count',)
        read_only_fields = ('email', 'id', 'username', 'first_name',
                            'last_name',)

    def get_recipes(self, instance):
        request = self.context.get('request')
        recipes_limit = request.query_params.get('recipes_limit')
        recipes = Recipe.objects.filter(author=instance)
        if recipes_limit:
            recipes_limit = int(recipes_limit)
            recipes = recipes[:recipes_limit]
        context = {'request': request}
        return RecipeInSubscriptionsSerializer(
            recipes,
            context=context,
            many=True
        ).data

    def get_recipes_count(self, instance):
        return Recipe.objects.filter(author=instance).count()

    def get_is_subscribed(self, instance):
        return True


class SubscribeCreateSerializer(ModelSerializer):
    user = PrimaryKeyRelatedField(queryset=User.objects.all())
    author = PrimaryKeyRelatedField(queryset=User.objects.all())

    class Meta:
        model = Subscribe
        fields = ('user', 'author')
        validators = [
            UniqueTogetherValidator(
                queryset=Subscribe.objects.all(),
                fields=('user', 'author'),
                message='Вы уже подписаны на этого пользователя',
            )
        ]

    def validate(self, value):
        user = self.context.get('request').user
        if user == value:
            raise ValidationError(
                'Вы не можете подписаться на самого себя!'
            )
        return value
