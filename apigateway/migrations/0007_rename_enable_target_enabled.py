# Generated by Django 3.2.9 on 2023-03-04 23:20

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('apigateway', '0006_target_enable'),
    ]

    operations = [
        migrations.RenameField(
            model_name='target',
            old_name='enable',
            new_name='enabled',
        ),
    ]
