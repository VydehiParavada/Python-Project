# Generated by Django 5.1.2 on 2024-11-04 04:57

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('DjTraders', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='customer',
            options={'managed': True},
        ),
        migrations.AlterModelOptions(
            name='product',
            options={'managed': True},
        ),
    ]
