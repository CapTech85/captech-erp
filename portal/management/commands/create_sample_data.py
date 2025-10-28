# portal/management/commands/create_sample_data.py
from django.apps import apps
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

Company = apps.get_model("core", "Company")
Customer = apps.get_model("core", "Customer")
Invoice = apps.get_model("core", "Invoice")
InvoiceItem = apps.get_model("core", "InvoiceItem")


class Command(BaseCommand):
    help = "Create sample company, customers and invoices for local dev"

    def handle(self, *args, **options):
        with transaction.atomic():
            company = Company.objects.create(name="Demo Company")
            self.stdout.write(f"Company created: {company.id}")
            # create customers
            customers = []
            for i in range(1, 6):
                c = Customer.objects.create(
                    company=company, name=f"Client {i}", email=f"client{i}@example.com"
                )
                customers.append(c)
            # create 12 months of invoices for first customer
            today = timezone.now().date()
            for m in range(12):
                dt = today.replace(day=1) - timezone.timedelta(days=30 * m)
                inv = Invoice.objects.create(
                    company=company,
                    customer=customers[m % len(customers)],
                    number=f"INV-{m+1:03d}",
                    issue_date=dt,
                    status="ISSUED",
                    due_at=dt + timezone.timedelta(days=30),
                )
                # one item
                InvoiceItem.objects.create(
                    invoice=inv,
                    description="Service",
                    quantity=1,
                    unit_price_cents=10000,
                    vat_rate=20,
                )
            self.stdout.write("Created sample invoices.")
