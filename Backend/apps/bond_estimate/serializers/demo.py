"""
Demo model for bond_estimate app.
This file demonstrates basic Django model structure.
"""
from django.db import models

class DemoModel(models.Model):
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
