"""
Models package for bond_estimate app.
You can define your Django ORM models here.
"""
from django.db import models

class ExampleModel(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name
