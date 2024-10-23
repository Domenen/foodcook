import csv
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from recipes.models import Ingredient


class Command(BaseCommand):

    def handle(self, *args, **kwargs):
        csv_file = Path(settings.FILE_PATH_INGREDIENTS / 'ingredients.csv')

        try:
            with open(csv_file, 'r', encoding='utf-8') as file:
                reader = csv.reader(file)
                ingredients = [
                    Ingredient(
                        name=name.strip(),
                        measurement_unit=measurement_unit.strip()
                    )
                    for name, measurement_unit in reader
                ]
                Ingredient.objects.bulk_create(
                    ingredients, ignore_conflicts=True
                )

                self.stdout.write(self.style.SUCCESS(
                    'Ингредиенты успешно загружены.'
                ))

        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(
                f'Файл не найден: '
                f'{settings.FILE_PATH_INGREDIENTS}/ingredients.csv'
            ))
        except Exception as e:
            self.stdout.write(self.style.ERROR(
                f'Ошибка при открытии файла: {str(e)}'
            ))
