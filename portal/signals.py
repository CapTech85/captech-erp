# portal/signals.py
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from core.models import Invoice  # adapte si Payment existe
from .services import invalidate_dashboard_cache

@receiver(post_save, sender=Invoice)
@receiver(post_delete, sender=Invoice)
def invoice_changed(sender, instance, **kwargs):
    company = getattr(instance, "company", None)
    if company:
        invalidate_dashboard_cache(company.id)

# If you have Payment model
#@receiver(post_save, sender=Payment)
#@receiver(post_delete, sender=Payment)
#def payment_changed(sender, instance, **kwargs):
#    company = getattr(instance, "company", None)
#    if company:
#        invalidate_dashboard_cache(company.id)
