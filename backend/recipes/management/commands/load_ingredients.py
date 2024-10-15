import csv
from pathlib import Path

from django.core.management.base import BaseCommand

from ...models import Ingredient
from foodgram.settings import FILE_PATH_INGREDIENTS


class Command(BaseCommand):

    def handle(self, *args, **kwargs):
        csv_file = Path(FILE_PATH_INGREDIENTS / 'ingredients.csv')

        with open(csv_file, 'r', encoding='utf-8') as file:
            reader = csv.reader(file)
            for row in reader:
                if len(row) == 2:
                    name, measurement_unit = row
                    name = name.strip()
                    measurement_unit = measurement_unit.strip()

                    ingredient, created = Ingredient.objects.get_or_create(
                        name=name, measurement_unit=measurement_unit
                    )
                    if created:
                        self.stdout.write(self.style.SUCCESS(
                            f"Added: {name} ({measurement_unit})")
                        )
                    else:
                        self.stdout.write(self.style.WARNING(
                            f"Skipped (already exists): {name} ({measurement_unit})")
                        )
                else:
                    self.stdout.write(self.style.ERROR(
                        f"Skipped (invalid format): {row}")
                    )
