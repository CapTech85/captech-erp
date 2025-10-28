# portal/tests/test_export_enqueue.py
from unittest.mock import MagicMock, patch

from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from core.models import Company, Customer, Invoice, InvoiceItem


class ExportEnqueueTest(TestCase):
    def setUp(self):
        self.company = Company.objects.create(name="ExportCo")
        self.customer = Customer.objects.create(company=self.company, name="C1")
        self.inv = Invoice.objects.create(
            company=self.company,
            customer=self.customer,
            number="INV-ENQ-1",
            issue_date=timezone.now().date(),
            status="ISSUED",
        )
        InvoiceItem.objects.create(
            invoice=self.inv,
            description="I",
            quantity=1,
            unit_price_cents=10000,
            vat_rate=20,
        )
        self.client = Client()

    @patch("django_rq.get_queue")
    def test_enqueue_export_calls_queue(self, mock_get_queue):
        fake_queue = MagicMock()
        fake_job = MagicMock()
        fake_job.id = "job-123"
        fake_queue.enqueue.return_value = fake_job
        mock_get_queue.return_value = fake_queue

        url = reverse("portal:invoice_enqueue_export", args=[self.inv.pk])
        resp = self.client.get(url)
        # redirection vers la liste des factures (implémentation fournie)
        self.assertEqual(resp.status_code, 302)
        fake_queue.enqueue.assert_called()
        args = fake_queue.enqueue.call_args[0]
        # le premier arg est la fonction heavy_export_invoice (callable)
        self.assertTrue(callable(args[0]))
        # le second argument devrait être l'invoice pk
        self.assertEqual(args[1], self.inv.pk)
