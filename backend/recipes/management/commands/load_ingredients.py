import csv
from pathlib import Path

from django.core.management.base import BaseCommand

from recipes.models import Ingredient
from foodgram.settings import FILE_PATH_INGREDIENTS


class Command(BaseCommand):

    def handle(self, *args, **kwargs):
        csv_file = Path(FILE_PATH_INGREDIENTS / 'ingredients.csv')
        if csv_file.exists():

            with open(csv_file, 'r', encoding='utf-8') as file:
                reader = csv.reader(file)
                for row in reader:
                    name = row[0].strip()
                    measurement_unit = row[1].strip()

                    created = Ingredient.objects.bulk_create(
                        objs=[Ingredient(
                            name=name,
                            measurement_unit=measurement_unit
                        )for name in row],
                        ignore_conflicts=True
                    )
                    if created:
                        self.stdout.write(self.style.SUCCESS(
                            f'Добавленно: {name} ({measurement_unit})')
                        )
                    elif not created:
                        self.stdout.write(self.style.SUCCESS(
                            f'Уже есть: {name} ({measurement_unit})')
                        )

                    else:
                        self.stdout.write(self.style.ERROR(
                            f'Проблемы с форматом: {row}, {measurement_unit}'
                        ))
        else:
            self.stdout.write(self.style.ERROR(
                f'Не найден {FILE_PATH_INGREDIENTS}/ingredients.csv'
            ))
