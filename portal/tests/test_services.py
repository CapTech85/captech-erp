# portal/tests/test_services.py
from decimal import Decimal
from django.test import TestCase
from core.models import Customer, Invoice, InvoiceItem
from portal.services import compute_dashboard

class DashboardServiceTest(TestCase):
    def setUp(self):
        # créer company et client simples (adapter selon ton modèle)
        company = self._create_company()
        self.company = company
        # create a customer
        c = Customer.objects.create(company=company, name="Client Test")
        # create a couple of invoices/invoiceitems
        inv1 = Invoice.objects.create(company=company, customer=c, number="INV-1", issue_date="2025-01-01", status="ISSUED")
        InvoiceItem.objects.create(invoice=inv1, description="Item", quantity=1, unit_price_cents=10000, vat_rate=20)

    def _create_company(self):
        # adapte selon ton model Company
        from core.models import Company
        return Company.objects.create(name="Test Company")

    def test_compute_dashboard_keys(self):
        data = compute_dashboard(self.company, use_cache=False)
        assert "cash_balance" in data
        assert "ca_series" in data
        assert isinstance(data["ca_series"], list)
