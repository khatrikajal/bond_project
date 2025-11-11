"""
Demo Django signal for bond_estimate app.
This is a placeholder to show signal usage.
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User

@receiver(post_save, sender=User)
def demo_signal(sender, instance, created, **kwargs):
    if created:
        print(f"Demo Signal: New user created -> {instance.username}")
