# Generated by Django 3.2.9 on 2023-01-01 06:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('apigateway', '0002_auto_20221117_0856'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='api',
            name='scheme',
        ),
        migrations.AddField(
            model_name='upstream',
            name='scheme',
            field=models.CharField(choices=[('http', 'Http'), ('https', 'Https'), ('http+unix', 'Unitx')], default='http', max_length=64),
        ),
        migrations.AlterField(
            model_name='upstream',
            name='alias',
            field=models.CharField(default='', max_length=64, unique=True),
        ),
    ]