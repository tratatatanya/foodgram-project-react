import json

from django.core.management.base import BaseCommand
from recipes.models import Ingredient


class Command(BaseCommand):
    def handle(self, *args, **options):

        with open("./ingredients.json", "rb") as f:
            data = json.load(f)

            for val in data:
                ingredient = Ingredient()
                ingredient.name = val["name"]
                ingredient.measurement_unit = val["measurement_unit"]
                ingredient.save()
        print("finished")
