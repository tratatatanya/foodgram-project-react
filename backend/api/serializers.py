from rest_framework.serializers import (ModelSerializer,
                                        ReadOnlyField, IntegerField,
                                        SerializerMethodField,
                                        PrimaryKeyRelatedField)
from djoser.serializers import UserCreateSerializer, UserSerializer
from drf_extra_fields.fields import Base64ImageField
from rest_framework.validators import UniqueTogetherValidator, ValidationError

from users.models import User, Subscribe
from recipes.models import (Ingredient, Recipe, Tag, Favorite,
                            IngredientInRecipe, Cart, TagsInRecipes)


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
        request = self.context.get('request')
        if request.user.is_anonymous:
            return False
        user = request.user
        subscribed = instance.subscriber.filter(user=instance, author=user)
        return subscribed.exists()


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
        validators = [
            UniqueTogetherValidator(
                queryset=User.objects.all(), fields=["username", "email"]
            )
        ]

    def validate_username(self, value):
        if value.lower() == "me":
            raise ValidationError('username не может быть "me"')
        return value


class TagSerializer(ModelSerializer):

    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug')


class IngredientSerializer(ModelSerializer):

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class IngredientInRecipeSerializer(ModelSerializer):
    id = PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(),
        source='ingredient'
    )
    amount = IntegerField()

    class Meta:
        model = IngredientInRecipe
        fields = ('id', 'amount',)


class RecipeSerializer(ModelSerializer):
    tags = TagSerializer(many=True)
    author = CustomUserSerializer(read_only=True)
    image = Base64ImageField()
    is_favorited = SerializerMethodField()
    is_in_shopping_cart = SerializerMethodField()
    ingredients = IngredientInRecipeSerializer(
        source='recipe',
        many=True,
        required=True
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


class AddRecipeSerializer(ModelSerializer):
    tags = PrimaryKeyRelatedField(
        many=True,
        queryset=Tag.objects.all()
    )
    ingredients = IngredientInRecipeSerializer(many=True)
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
            'cooking_time'
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
        print(validated_data)
        recipe = Recipe.objects.create(author=author, **validated_data)
        self.add_ingredients(ingredients, recipe)
        recipe.tags.set(tags)
        return recipe

    def update(self, recipe, validated_data):
        recipe.name = validated_data.get('name', recipe.name)
        recipe.text = validated_data.get('text', recipe.text)
        recipe.image = validated_data.get('image', recipe.image)
        recipe.cooking_time = validated_data.get(
            'cooking_time', recipe.cooking_time
        )
        tags = validated_data.pop('tags')
        recipe.tags.set(tags) if tags else None
        ingredients = validated_data.pop('ingredients')
        recipe.ingredients.clear()
        self.add_ingredients(ingredients, recipe)
        recipe.save()
        return recipe

    def to_representation(self, recipe):
        return RecipeSerializer(
            recipe, context={'request': self.context.get('request')}
        ).data


class RecipeInFavoriteSerializer(ModelSerializer):

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class FavoriteSerializer(ModelSerializer):
    recipe = PrimaryKeyRelatedField(queryset=Recipe.objects.all())
    user = PrimaryKeyRelatedField(queryset=User.objects.all())

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
    recipe = PrimaryKeyRelatedField(queryset=Recipe.objects.all())
    user = PrimaryKeyRelatedField(queryset=User.objects.all())

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
        return RecipeInFavoriteSerializer(instance.recipe).data


class RecipeInSubscriptionsSerializer(ModelSerializer):

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class SubscriptionSerializer(ModelSerializer):
    recipes = RecipeInSubscriptionsSerializer(many=True)
    is_subscribed = SerializerMethodField()
    recipes_count = ReadOnlyField(source='author.recipe.count')

    class Meta:
        model = Subscribe
        fields = ('email', 'id', 'username', 'first_name',
                  'last_name', 'is_subscribed', 'recipes', 'recipes_count',)

    def validate(self, data):
        user = self.context.get('request').user
        author = self.context.get('author_id')
        if user.id == int(author):
            raise ValidationError('Нельзя подписаться на самого себя')
        if Subscribe.objects.filter(user=user, author=author).exists():
            raise ValidationError('Вы уже подписаны на данного пользователя')
        return data

    def get_recipes(self, instance):
        recipes = instance.author.recipe.all()
        return RecipeInSubscriptionsSerializer(recipes, many=True).data

    def get_is_subscribed(self, instance):
        subscribe = Subscribe.objects.filter(
            user=self.context.get('request').user,
            author=instance.author
        )
        if subscribe:
            return True
        return False


class SubscribeSerializer(ModelSerializer):
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

    def validate_following(self, value):
        user = self.context.get('request').user
        if user == value:
            raise ValidationError(
                'Вы не можете подписаться на самого себя!'
            )
        return value
