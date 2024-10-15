# Generated by Django 3.2.4 on 2024-10-15 08:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='recipeingredient',
            options={'verbose_name': 'Ингредиент в рецепте', 'verbose_name_plural': 'Ингредиенты в рецептах'},
        ),
        migrations.AddField(
            model_name='recipe',
            name='short_url',
            field=models.CharField(blank=True, max_length=10, null=True, unique=True, verbose_name='Короткая ссылка'),
        ),
    ]
