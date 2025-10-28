# portal/views_export.py
import django_rq
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse

from core.models import Invoice

from .tasks import heavy_export_invoice


def enqueue_export(request, pk: int):
    """
    Enqueue la tâche heavy_export_invoice sur la queue 'default'.
    """
    invoice = get_object_or_404(Invoice, pk=pk)
    q = django_rq.get_queue("default")
    job = q.enqueue(heavy_export_invoice, invoice.pk)
    messages.success(request, f"Export placé en file (job id: {job.id})")
    return redirect(reverse("portal:invoices"))
