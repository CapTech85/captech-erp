# portal/tasks.py
"""
Tâches background liées à l'export / traitements longs.
"""
import os

from django.conf import settings
from django.utils import timezone

from core.models import Invoice


def heavy_export_invoice(invoice_pk: int) -> str:
    """
    Tâche longue (exécutée par RQ) qui exporte une facture.
    Implémentation minimale : crée un fichier texte dans MEDIA_ROOT/exports/
    pour prouver que la tâche a bien été exécutée par le worker.

    Remarque : remplacer par génération PDF réelle si tu veux.
    Retourne le chemin du fichier écrit.
    """
    inv = Invoice.objects.get(pk=invoice_pk)
    out_dir = os.path.join(settings.MEDIA_ROOT, "exports")
    os.makedirs(out_dir, exist_ok=True)
    filename = os.path.join(
        out_dir, f"invoice_{inv.pk}_{timezone.now().strftime('%Y%m%d%H%M%S')}.txt"
    )
    content = (
        f"Export de la facture {inv.number}\n"
        f"Entreprise: {inv.company}\n"
        f"Client: {getattr(inv.customer, 'name', '—')}\n"
        f"Issue date: {inv.issue_date}\n"
    ).encode("utf-8")
    with open(filename, "wb") as fh:
        fh.write(content)
    return filename
