# portal/tests/test_signals.py
from django.test import TestCase
from django.core.cache import cache
from django.apps import apps
from django.utils import timezone

class SignalsTest(TestCase):
    def test_invoice_save_invalidates_cache(self):
        Company = apps.get_model('core','Company')
        Customer = apps.get_model('core','Customer')
        Invoice = apps.get_model('core','Invoice')
        InvoiceItem = apps.get_model('core','InvoiceItem')

        company = Company.objects.create(name='TestCo')
        customer = Customer.objects.create(company=company, name='C')
        inv = Invoice.objects.create(company=company, customer=customer,
                                     number='I-SIGNAL', issue_date=timezone.now().date(),
                                     status='ISSUED')
        # create at least one item if model requires it
        if any(f.name == 'invoice' for f in InvoiceItem._meta.fields):
            InvoiceItem.objects.create(invoice=inv, description='Item', quantity=1, unit_price_cents=1000, vat_rate=20)

        key = f"dash:{company.id}"
        cache.set(key, {'x':1}, 600)
        assert cache.get(key) is not None
        inv.save()
        assert cache.get(key) is None
