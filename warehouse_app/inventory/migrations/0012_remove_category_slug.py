# Generated by Django 5.1.6 on 2025-02-16 18:27

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0011_category_product_category'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='category',
            name='slug',
        ),
    ]
