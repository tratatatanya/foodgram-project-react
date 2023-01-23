from django.contrib import admin

from .models import Tag, Ingredient, IngredientInRecipe, Recipe, TagsInRecipes, Cart


class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'color', 'slug')
    search_fields = ('name', 'color', 'slug')


class IngredientAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'measurement_unit')
    list_filter = ('name', 'measurement_unit')
    search_fields = ('name',)


class IngredientInRecipeAdmin(admin.ModelAdmin):
    list_display = ('id', 'recipe', 'ingredient', 'amount')
    search_fields = ('recipe', 'ingredient', 'amount')


class TagsInLine(admin.StackedInline):
    model = TagsInRecipes


class IngredientsInLine(admin.StackedInline):
    model = IngredientInRecipe


class RecipeAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'text', 'cooking_time', 'pub_date',
        'display_ingredients', 'display_tags', 'favorites'
    )
    list_filter = ('name', 'author', 'tags')
    inlines = (TagsInLine, IngredientsInLine)

    def favorites(self, obj):
        return obj.favorite_recipe.all().count()
    favorites.short_description = 'В избранном'


class CartAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe')


admin.site.register(Tag, TagAdmin)
admin.site.register(Ingredient, IngredientAdmin)
admin.site.register(IngredientInRecipe, IngredientInRecipeAdmin)
admin.site.register(Recipe, RecipeAdmin)
admin.site.register(Cart, CartAdmin)
