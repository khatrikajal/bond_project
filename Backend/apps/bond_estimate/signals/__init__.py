"""
Signals package for bond_estimate app.
Use Django signals like post_save or pre_delete here.
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings

@receiver(post_save)
def example_signal(sender, **kwargs):
    pass  # placeholder for signal handlers
