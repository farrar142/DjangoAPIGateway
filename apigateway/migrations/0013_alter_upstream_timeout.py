# Generated by Django 3.2.9 on 2023-03-07 04:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('apigateway', '0012_auto_20230306_1928'),
    ]

    operations = [
        migrations.AlterField(
            model_name='upstream',
            name='timeout',
            field=models.PositiveIntegerField(default=10),
        ),
    ]