# Generated by Django 5.1.6 on 2025-02-16 15:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0009_product_ean'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='ean',
            field=models.CharField(blank=True, help_text='Kod EAN', max_length=13, null=True),
        ),
        migrations.AlterField(
            model_name='product',
            name='weight',
            field=models.CharField(blank=True, help_text='Waga w kilogramach', max_length=4, null=True),
        ),
    ]
