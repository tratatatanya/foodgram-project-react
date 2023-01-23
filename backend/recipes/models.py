from colorfield.fields import ColorField
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import UniqueConstraint

from users.models import User
from .validators import validate_time


class Tag(models.Model):
    name = models.CharField(verbose_name='Тэг', max_length=200, unique=True)
    color = ColorField(verbose_name='Цвет', default='#49B64E', unique=True)
    slug = models.SlugField(verbose_name='Ссылка', unique=True,)

    class Meta:
        verbose_name = 'Тэг'
        verbose_name_plural = 'Тэги'

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    name = models.CharField(
        verbose_name='Название ингредиента',
        max_length=200,
        unique=True,
        blank=False
    )
    measurement_unit=models.CharField(
        verbose_name='Единица измерения',
        max_length=200,
        blank=False
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'


class Recipe(models.Model):
    name = models.CharField(
        verbose_name='Название блюда',
        max_length=200,
        blank=False
    )
    text = models.TextField(verbose_name='Описание')
    image = models.ImageField(
        verbose_name='Фото блюда',
        blank=False
    )
    cooking_time = models.IntegerField(
        verbose_name='Время приготовления',
        validators=[validate_time]
    )
    tags = models.ManyToManyField(
        Tag,
        verbose_name='Тэги',
        blank=True,
        through='recipes.TagsInRecipes',
        related_name='recipes'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор рецепта',
        related_name='recipes'
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through='recipes.IngredientInRecipe',
        related_name='recipes',
    )
    pub_date = models.DateTimeField(auto_now_add=True)

    def display_tags(self):
        return ', '.join([tag.name for tag in self.tags.all()])
    display_tags.short_description = 'Тэги'

    def display_ingredients(self):
        return ', '.join([ingredient.name for ingredient in self.ingredients.all()])
    display_ingredients.short_description = 'Ингредиенты'

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['-pub_date']
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'


class TagsInRecipes(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        related_name='recipe_tags',
        on_delete=models.CASCADE,
    )
    tags = models.ForeignKey(
        Tag,
        related_name='recipe_tags',
        on_delete=models.DO_NOTHING
    )


class IngredientInRecipe(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        related_name='recipe',
        on_delete=models.CASCADE,
    )
    ingredient = models.ForeignKey(
        Ingredient,
        related_name='ingredient',
        on_delete=models.CASCADE,
    )
    amount = models.PositiveIntegerField(
        validators=[MinValueValidator(
            1,
            'Указывайте ингредиенты, которые действительно нужны!'
        )]
    )

    class Meta:
        verbose_name = 'Ингредиент в рецепте'
        verbose_name_plural = 'Ингредиенты в рецепте'


class Favorite(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favorite',
        verbose_name='Пользователь',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='favorite_recipe',
        verbose_name='Избранный рецепт',
    )

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=['user', 'recipe'], name='recipe_in_favorite_unique'
            )
        ]
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'


class Cart(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='shopping_cart',
        verbose_name='Пользователь',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='recipe_in_shopping_cart',
        verbose_name='Рецепт',
    )

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=['user', 'recipe'], name='recipe_in_shopping_cart'
            )
        ]
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Список покупок'
