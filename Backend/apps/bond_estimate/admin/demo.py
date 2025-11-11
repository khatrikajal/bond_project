"""
Demo admin file for bond_estimate app.
Shows how to register a model in Django admin.
"""
from django.contrib import admin
from django.contrib.auth.models import User

@admin.register(User)
class DemoAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'is_staff')
