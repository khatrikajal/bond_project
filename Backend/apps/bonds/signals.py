# G:\bond_platform\Backend\apps\bonds\signals.py
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import ISINBasicInfo, ContactMessage
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.conf import settings
from .services.bond_elastic_service import BondElasticService





@receiver(post_save, sender=ContactMessage)
def send_thank_you_email(sender, instance, created, **kwargs):
    if created:
        # Render HTML email template
        html_message = render_to_string('emails/contact_thank_you.html', {'contact': instance})
        
        email = EmailMessage(
            subject="Thank you for contacting us",
            body=html_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[instance.email]
        )
        email.content_subtype = "html"  # Important for HTML
        email.send(fail_silently=True)
        