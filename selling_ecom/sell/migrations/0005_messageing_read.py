# Generated by Django 5.0.6 on 2024-05-27 10:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sell', '0004_material_product_size_product_material'),
    ]

    operations = [
        migrations.AddField(
            model_name='messageing',
            name='read',
            field=models.BooleanField(default=False),
        ),
    ]
