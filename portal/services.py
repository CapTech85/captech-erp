# portal/services.py
"""
Services pour le Dashboard : calcul des KPIs synthétiques.
Toutes les valeurs renvoyées sont des Decimals quand c'est monétaire,
ou des listes/dicts quand c'est structurel.
"""

from decimal import Decimal, ROUND_HALF_UP
from django.utils import timezone
from django.db.models import Sum
from collections import defaultdict
from datetime import date, timedelta, datetime

from core.models import Invoice, InvoiceItem, TurnoverEntry, Customer
from core.utils import invoice_total  # utilitaire existant dans le projet

Q2 = Decimal("0.01")

def _to_eur(cents):
  """Convertit des centimes (int/Decimal) en Decimal euros, arrondis 2 décimales."""
  if cents is None:
    return Decimal("0.00")
  return (Decimal(cents) / Decimal(100)).quantize(Q2, rounding=ROUND_HALF_UP)

def _decimal(v):
  """Assure que la valeur est Decimal à 2 décimales."""
  return (Decimal(v) if not isinstance(v, Decimal) else v).quantize(Q2, rounding=ROUND_HALF_UP)

def compute_dashboard(company, page_size=5):
  """Retourne un dict contenant les valeurs nécessaires au Dashboard pour la company donnée."""
  today = timezone.now().date()
  # Solde "cash" : si tu as des comptes bancaires, remplace cette logique.
  # Ici on utilise TurnoverEntry.amount (champ Decimal) comme approximation/entrée manuelle.
  cash_agg = TurnoverEntry.objects.filter(company=company).aggregate(total=Sum('amount'))
  cash_balance = _decimal(cash_agg.get('total') or Decimal("0.00"))

  # CA mois courant
  start_month = today.replace(day=1)
  invoices_month = Invoice.objects.filter(company=company, issue_date__gte=start_month, status="ISSUED")
  ca_month = sum((invoice_total(inv) for inv in invoices_month), Decimal("0.00")).quantize(Q2)

  # Invoices ouvertes (ISSUED) et montant total open
  invoices_open_qs = Invoice.objects.filter(company=company, status="ISSUED")
  invoices_open_tot = sum((invoice_total(inv) for inv in invoices_open_qs), Decimal("0.00")).quantize(Q2)

  # clients > 30 jours (distincts)
  clients_over_30 = set()
  for inv in invoices_open_qs:
    if inv.due_at:
      age = (today - inv.due_at).days
      if age > 30:
        if inv.customer_id:
          clients_over_30.add(inv.customer_id)
  clients_over_30_count = len(clients_over_30)

  # Recent invoices (limit page_size)
  recent_invoices = list(Invoice.objects.filter(company=company).order_by("-issue_date")[:page_size])
  # enrichir avec montants
  for inv in recent_invoices:
    inv.computed_total = invoice_total(inv)

  # Aging buckets (par montant)
  aging = {"0_30": Decimal("0.00"), "31_60": Decimal("0.00"), "61_90": Decimal("0.00"), "gt_90": Decimal("0.00")}
  for inv in invoices_open_qs:
    amt = invoice_total(inv)
    age_days = (today - (inv.issue_date or today)).days
    if age_days <= 30:
      aging["0_30"] += amt
    elif age_days <= 60:
      aging["31_60"] += amt
    elif age_days <= 90:
      aging["61_90"] += amt
    else:
      aging["gt_90"] += amt
  # quantize
  for k in aging:
    aging[k] = aging[k].quantize(Q2)

  # Top customers (simple accumulation)
  top_map = defaultdict(Decimal)
  for inv in Invoice.objects.filter(company=company):
    if inv.customer_id:
      top_map[(inv.customer_id, getattr(inv.customer, "name", ""))] += invoice_total(inv)
  # order & format
  top_customers = sorted([{"id":cid, "name":name, "total":amt.quantize(Q2)} for (cid,name), amt in top_map.items()],
                         key=lambda x: x["total"], reverse=True)[:5]

  # CA last 12 months series (liste de 12 decimals, oldest->newest)
  series = []
  for i in range(11, -1, -1):
    # month start
    month = (today.replace(day=1) - timedelta(days=1)).replace(day=1)
    # compute by shifting months
    # simpler approach: compute start and end
    # build month start merception
    y = today.year
    m = today.month - i
    while m <= 0:
      m += 12
      y -= 1
    start = date(y, m, 1)
    if m == 12:
      end = date(y+1, 1, 1) - timedelta(days=1)
    else:
      end = date(y, m+1, 1) - timedelta(days=1)
    invs = Invoice.objects.filter(company=company, issue_date__gte=start, issue_date__lte=end, status="ISSUED")
    s = sum((invoice_total(inv) for inv in invs), Decimal("0.00")).quantize(Q2)
    series.append(s)

  return {
    "cash_balance": cash_balance,
    "ca_month": ca_month,
    "invoices_open_total": invoices_open_tot.quantize(Q2),
    "clients_over_30": clients_over_30_count,
    "recent_invoices": recent_invoices,
    "aging": aging,
    "top_customers": top_customers,
    "ca_series": series,  # oldest->newest
  }
