# portal/signals.py
from django.apps import apps as django_apps
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

# Import de la fonction d'invalidation (doit exister dans portal/services.py)
from .services import invalidate_dashboard_cache

# Récupère les modèles dynamiquement pour éviter ImportError si absent
Invoice = django_apps.get_model("core", "Invoice")
Payment = None
try:
    Payment = django_apps.get_model("core", "Payment")
except LookupError:
    Payment = None


@receiver(post_save, sender=Invoice)
def invoice_saved(sender, instance, **kwargs):
    company = getattr(instance, "company", None)
    if company:
        invalidate_dashboard_cache(company.id)


@receiver(post_delete, sender=Invoice)
def invoice_deleted(sender, instance, **kwargs):
    company = getattr(instance, "company", None)
    if company:
        invalidate_dashboard_cache(company.id)


# Si Payment existe, on connecte les handlers aussi
if Payment is not None:

    @receiver(post_save, sender=Payment)
    def payment_saved(sender, instance, **kwargs):
        company = getattr(instance, "company", None)
        if company:
            invalidate_dashboard_cache(company.id)

    @receiver(post_delete, sender=Payment)
    def payment_deleted(sender, instance, **kwargs):
        company = getattr(instance, "company", None)
        if company:
            invalidate_dashboard_cache(company.id)
