# Generated by Django 3.2.9 on 2023-02-05 17:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('apigateway', '0003_auto_20230101_0627'),
    ]

    operations = [
        migrations.AddField(
            model_name='consumer',
            name='identifier',
            field=models.CharField(default='', max_length=256),
        ),
    ]
