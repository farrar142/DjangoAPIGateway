from django.db import models

# Create your models here.
class RedirectionPage(models.Model):
    requested_path = models.CharField(max_length=512)
    target_path = models.URLField()
class TestModel(models.Model):
    name = models.CharField(max_length=32)