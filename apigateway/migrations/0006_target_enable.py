# Generated by Django 3.2.9 on 2023-03-04 23:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('apigateway', '0005_auto_20230304_2206'),
    ]

    operations = [
        migrations.AddField(
            model_name='target',
            name='enable',
            field=models.BooleanField(default=True),
        ),
    ]