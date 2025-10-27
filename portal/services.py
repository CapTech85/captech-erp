# portal/services.py
from decimal import Decimal, ROUND_HALF_UP
from collections import defaultdict
from datetime import date, timedelta

from django.core.cache import cache
from django.db.models import Sum
from django.utils import timezone

from core.models import Invoice, TurnoverEntry
from core.utils import invoice_total  # garde le calcul centralisé

Q2 = Decimal("0.01")

def _decimal(v):
    if v is None:
        return Decimal("0.00")
    return (v if isinstance(v, Decimal) else Decimal(v)).quantize(Q2, rounding=ROUND_HALF_UP)

def _month_bounds(today, months_back):
    # renvoie (start, end) du mois à months_back (0 = mois courant)
    y = today.year
    m = today.month - months_back
    while m <= 0:
        m += 12
        y -= 1
    start = date(y, m, 1)
    if m == 12:
        end = date(y + 1, 1, 1) - timedelta(days=1)
    else:
        end = date(y, m + 1, 1) - timedelta(days=1)
    return start, end

def invalidate_dashboard_cache(company_id):
    cache.delete(f"dash:{company_id}")

def compute_dashboard(company, page_size=5, use_cache=True, ttl=600):
    """
    Calcule les KPIs du dashboard.
    - Cache par company (TTL par défaut: 10 min)
    - Optimisations ORM (select_related)
    """
    cache_key = f"dash:{company.id}"
    if use_cache:
        cached = cache.get(cache_key)
        if cached is not None:
            return cached

    today = timezone.now().date()

    # --- Trésorerie estimée (remplace par comptes bancaires si tu en as) ---
    cash_agg = TurnoverEntry.objects.filter(company=company).aggregate(total=Sum('amount'))
    cash_balance = _decimal(cash_agg.get('total') or Decimal("0.00"))

    # --- CA mois courant ---
    start_month = today.replace(day=1)
    invoices_month = (Invoice.objects
                      .filter(company=company, issue_date__gte=start_month, status="ISSUED")
                      .select_related("customer"))
    ca_month = sum((invoice_total(inv) for inv in invoices_month), Decimal("0.00")).quantize(Q2)

    # --- Factures ouvertes ---
    invoices_open_qs = (Invoice.objects
                        .filter(company=company, status="ISSUED")
                        .select_related("customer"))
    invoices_open_total = sum((invoice_total(inv) for inv in invoices_open_qs), Decimal("0.00")).quantize(Q2)

    # clients > 30j (distinct)
    clients_over_30 = set()
    for inv in invoices_open_qs:
        if inv.due_at:
            age = (today - inv.due_at).days
            if age > 30 and inv.customer_id:
                clients_over_30.add(inv.customer_id)
    clients_over_30_count = len(clients_over_30)

    # --- Factures récentes (évite N+1) ---
    recent_invoices = list(
        Invoice.objects.filter(company=company).select_related("customer").order_by("-issue_date")[:page_size]
    )
    for inv in recent_invoices:
        inv.computed_total = invoice_total(inv)  # pas d'underscore -> template-safe

    # --- Aging buckets ---
    aging = {"0_30": Decimal("0.00"), "31_60": Decimal("0.00"),
             "61_90": Decimal("0.00"), "gt_90": Decimal("0.00")}
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
    for k in aging:
        aging[k] = aging[k].quantize(Q2)

    # --- Top clients (90j) ---
    top_map = defaultdict(Decimal)
    start_90 = today - timedelta(days=90)
    for inv in Invoice.objects.filter(company=company, issue_date__gte=start_90).select_related("customer"):
        if inv.customer_id:
            top_map[(inv.customer_id, getattr(inv.customer, "name", ""))] += invoice_total(inv)
    top_customers = sorted(
        [{"id": cid, "name": name, "total": amt.quantize(Q2)} for (cid, name), amt in top_map.items()],
        key=lambda x: x["total"], reverse=True
    )[:5]

    # --- Série CA 12 mois ---
    ca_series = []
    for i in range(11, -1, -1):
        start, end = _month_bounds(today, i)
        invs = Invoice.objects.filter(company=company, issue_date__gte=start, issue_date__lte=end, status="ISSUED")
        s = sum((invoice_total(inv) for inv in invs), Decimal("0.00")).quantize(Q2)
        ca_series.append(s)

    data = {
        "cash_balance": cash_balance,
        "ca_month": ca_month,
        "invoices_open_total": invoices_open_total,
        "clients_over_30": clients_over_30_count,
        "recent_invoices": recent_invoices,
        "aging": aging,
        "top_customers": top_customers,
        "ca_series": ca_series,
    }
    if use_cache:
        cache.set(cache_key, data, ttl)
    return data
