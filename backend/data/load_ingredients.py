import csv

from django.core.management.base import BaseCommand

from ..recipes.models import Ingredient


from ...models import (
    Category,
    Comment,
    Genre,
    Review,
    Title,
    User,
)

FIELD_MAPPINGS = {
    'titles.csv': {'category': 'category_id'},
    'comments.csv': {'author': 'author_id'},
    'review.csv': {'author': 'author_id'},
}

DATA_FILES = [
    ('users.csv', User),
    ('category.csv', Category),
    ('genre.csv', Genre),
    ('titles.csv', Title),
    ('review.csv', Review),
    ('comments.csv', Comment),
]


class Command(BaseCommand):
    def handle(self, *args, **options):
        def load_data_from_csv(csv_file, model):
            csv_file_path = Path(STATICFILES_DIRS[0]) / 'data' / csv_file
            field_mapping = FIELD_MAPPINGS.get(csv_file, {})

            with open(csv_file_path, 'r', encoding='utf-8') as data_csv_file:
                reader = csv.DictReader(data_csv_file)

                for row in reader:
                    for old_field, new_field in field_mapping.items():
                        row[new_field] = row.pop(old_field)

                    try:
                        obj, created = model.objects.update_or_create(
                            id=row['id'],
                            defaults=row
                        )
                    except Exception as e:
                        self.stderr.write(
                            self.style.ERROR(
                                f'Ошибка при обработке строки {row}: {e}'
                            )
                        )
                        continue

                self.stdout.write(
                    self.style.SUCCESS(
                        f'Данные успешно загружены из файла {csv_file} '
                        f'в модель {model.__name__}'
                    )
                )

        for csv_file, model in DATA_FILES:
            try:
                load_data_from_csv(csv_file, model)
            except Exception as e:
                self.stderr.write(
                    self.style.ERROR(
                        f'Ошибка загрузки данных из файла {csv_file}: {e}'
                    )
                )


class Command(BaseCommand):
    help = 'Loads ingredients from a CSV file'

    def add_arguments(self, parser):
        parser.add_argument('csv_file',
                            type=str,
                            help='The path to the CSV file'
                            )

    def handle(self, *args, **kwargs):
        csv_file = kwargs['csv_file']

        with open(csv_file, 'r', encoding='utf-8') as file:
            reader = csv.reader(file)
            for row in reader:
                if len(row) == 2:
                    name, unit = row
                    name = name.strip()
                    unit = unit.strip()

                    ingredient, created = Ingredient.objects.get_or_create(
                        name=name, unit=unit
                    )
                    if created:
                        self.stdout.write(self.style.SUCCESS(
                            f"Added: {name} ({unit})")
                        )
                    else:
                        self.stdout.write(self.style.WARNING(
                            f"Skipped (already exists): {name} ({unit})")
                        )
                else:
                    self.stdout.write(self.style.ERROR(
                        f"Skipped (invalid format): {row}")
                    )
