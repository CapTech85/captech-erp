# portal/tests/test_services_insights.py
from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from core.models import Company, Customer, Invoice, InvoiceItem
from portal.services_insights import compute_insights


class InsightsRulesTest(TestCase):
    def setUp(self):
        self.company = Company.objects.create(name="Ico")
        self.client_a = Customer.objects.create(company=self.company, name="Client A")
        self.today = timezone.now().date()

    def test_low_margin_detected_when_large_discount(self):
        inv = Invoice.objects.create(
            company=self.company,
            customer=self.client_a,
            number="LMI-1",
            issue_date=self.today,
            status="ISSUED",
        )
        # base HT = 100.00, discount 30% => discount_ratio 30%
        InvoiceItem.objects.create(
            invoice=inv,
            description="X",
            quantity=1,
            unit_price_cents=10000,
            vat_rate=20,
            discount_pct=30,
        )
        insights = compute_insights(
            self.company, low_margin_threshold_pct=20, lost_months=6
        )
        types = [i["type"] for i in insights]
        self.assertIn("low_margin_invoice", types)

    def test_lost_client_rule(self):
        # facture ancienne (7 mois)
        old_date = self.today - timedelta(days=30 * 7)
        inv = Invoice.objects.create(
            company=self.company,
            customer=self.client_a,
            number="OLD-1",
            issue_date=old_date,
            status="ISSUED",
        )
        InvoiceItem.objects.create(
            invoice=inv,
            description="Old",
            quantity=1,
            unit_price_cents=10000,
            vat_rate=20,
        )
        insights = compute_insights(
            self.company, low_margin_threshold_pct=50, lost_months=6
        )
        # Should find a lost_client insight
        found = [
            i
            for i in insights
            if i["type"] == "lost_client" and i["customer_id"] == self.client_a.pk
        ]
        self.assertTrue(len(found) >= 1)
