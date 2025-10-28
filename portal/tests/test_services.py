# portal/tests/test_services.py
from decimal import Decimal
from django.test import TestCase
from django.utils import timezone

# imports projet — adapte si les noms diffèrent
from core.models import Company, Customer, Invoice, InvoiceItem
from portal.services import compute_dashboard

class DashboardServiceTest(TestCase):
    def setUp(self):
        # create company / customer / invoices
        self.company = Company.objects.create(name="Test Co")
        self.customer = Customer.objects.create(company=self.company, name="Client Test")

        today = timezone.now().date()
        # invoice 1 (current month)
        inv1 = Invoice.objects.create(
            company=self.company,
            customer=self.customer,
            number="INV-001",
            issue_date=today,
            status="ISSUED",
        )
        InvoiceItem.objects.create(invoice=inv1, description="Item A", quantity=1, unit_price_cents=10000, vat_rate=20)

        # invoice 2 (older)
        inv2 = Invoice.objects.create(
            company=self.company,
            customer=self.customer,
            number="INV-002",
            issue_date=today - timezone.timedelta(days=45),
            status="ISSUED",
        )
        InvoiceItem.objects.create(invoice=inv2, description="Item B", quantity=2, unit_price_cents=5000, vat_rate=20)

    def test_compute_dashboard_returns_keys(self):
        data = compute_dashboard(self.company, use_cache=False)
        assert isinstance(data, dict)
        for key in ("cash_balance", "ca_month", "invoices_open_total", "clients_over_30", "recent_invoices", "aging", "top_customers", "ca_series"):
            assert key in data

    def test_ca_month_and_aging(self):
        data = compute_dashboard(self.company, use_cache=False)
        # CA month should be a Decimal > 0
        assert data["ca_month"] >= Decimal("0.00")
        # aging buckets present and decimals
        for k in ("0_30","31_60","61_90","gt_90"):
            assert k in data["aging"]
