# portal/services_insights.py
"""
Calcul d'insights pour le dashboard.
Contient des règles simples (extensibles) :
- marge faible : lorsqu'une facture applique une remise importante (proxy de marge)
- client perdu : client sans facturation depuis N mois
"""
from datetime import timedelta
from decimal import ROUND_HALF_UP, Decimal

from django.utils import timezone

from core.models import Customer, Invoice

Q2 = Decimal("0.01")


def _quantize(d):
    return (d if isinstance(d, Decimal) else Decimal(d)).quantize(
        Q2, rounding=ROUND_HALF_UP
    )


def compute_insights(company, low_margin_threshold_pct=20, lost_months=6):
    """
    Retourne une liste d'insights (dict).
    Paramètres :
      - low_margin_threshold_pct : seuil (%) de remise qui déclenche "marge faible"
      - lost_months : nombre de mois sans facturation pour considérer un client "perdu"

    NOTE : le modèle actuel ne contient pas de `unit_cost_cents`, on utilise donc la
    **remise appliquée** comme proxy de marge faible. Si tu ajoutes plus tard
    un champ coût, on pourra basculer sur une marge réelle coût/prix.
    """
    insights = []
    today = timezone.now().date()

    # --- Règle 1 : marge faible (proxy = remise importante) ---
    inv_qs = Invoice.objects.filter(
        company=company, status__in=["ISSUED", "PAID"]
    ).prefetch_related("items")
    for inv in inv_qs:
        subtotal = Decimal("0.00")
        discount_total = Decimal("0.00")
        for it in inv.items.all():
            q = Decimal(it.quantity)
            unit = Decimal(it.unit_price_cents) / Decimal(100)
            base = q * unit
            disc_pct = Decimal(it.discount_pct or 0) / Decimal(100)
            discount = base * disc_pct
            subtotal += base
            discount_total += discount

        # évite la division par zéro
        if subtotal > Decimal("0.00"):
            disc_ratio = (discount_total / subtotal) * Decimal("100")
            if disc_ratio >= Decimal(low_margin_threshold_pct):
                insights.append(
                    {
                        "type": "low_margin_invoice",
                        "title": "Marge faible",
                        "invoice_id": inv.pk,
                        "invoice_number": inv.number,
                        "discount_pct": float(_quantize(disc_ratio)),
                        "severity": "warning",
                        "message": f"Remise {float(_quantize(disc_ratio)):.1f}% sur la facture {inv.number}",
                    }
                )

    # --- Règle 2 : client perdu (pas de facture depuis N mois) ---
    cutoff = today - timedelta(days=30 * lost_months)  # approximation 30j/mois
    customers = Customer.objects.filter(company=company)
    for c in customers:
        last_inv = (
            Invoice.objects.filter(company=company, customer=c)
            .order_by("-issue_date")
            .first()
        )
        if last_inv:
            if last_inv.issue_date < cutoff:
                insights.append(
                    {
                        "type": "lost_client",
                        "title": "Client potentiellement perdu",
                        "customer_id": c.pk,
                        "customer_name": c.name,
                        "last_invoice_date": last_inv.issue_date.isoformat(),
                        "severity": "info",
                        "message": f"Aucune facturation depuis le {last_inv.issue_date.isoformat()} pour {c.name}",
                    }
                )
    return insights
