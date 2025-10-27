# portal/views_pdf.py
from decimal import Decimal, ROUND_HALF_UP
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
from .pdf_utils import link_callback

# === Helpers monnaie / arrondis ===
Q2 = Decimal("0.01")
D100 = Decimal("100")

def money(x) -> Decimal:
  return Decimal(x).quantize(Q2, rounding=ROUND_HALF_UP)

def cents_to_money(cents: int) -> Decimal:
  return (Decimal(cents) / D100).quantize(Q2, rounding=ROUND_HALF_UP)

# === Mocks de données (à remplacer par tes modèles réels) ===
def _fake_invoice(pk: int):
  return {
    "number": f"FAC-{pk:05d}",
    "issue_date": "2025-10-01",
    "company": {"name": "CapTech", "email": "info@captech.test"},
    "customer": {"name": "Client Démo", "billing_address": "1 rue Exemple\n75000 Paris", "vat_number": "FRXX..."},
    "items": [
      {"description": "Prestation A", "quantity": 2, "unit_price_cents": 1299, "vat_rate": 20, "discount_pct": 10},
      {"description": "Prestation B", "quantity": 1, "unit_price_cents": 5000, "vat_rate": 5.5, "discount_pct": 0},
    ],
  }

def _fake_quote(pk: int):
  return {
    "number": f"DEV-{pk:05d}",
    "issue_date": "2025-10-01",
    "valid_until": "2025-11-01",
    "company": {"name": "CapTech", "email": "info@captech.test"},
    "customer": {"name": "Prospect Démo", "billing_address": "2 avenue Test\n69000 Lyon", "vat_number": ""},
    "items": [
      {"description": "Mission découverte", "quantity": 1, "unit_price_cents": 30000, "vat_rate": 20, "discount_pct": 0},
      {"description": "Atelier cadrage (jour)", "quantity": 2, "unit_price_cents": 65000, "vat_rate": 20, "discount_pct": 5},
    ],
    "footer_note": "Devis valable 30 jours. Acompte 30% à la commande.",
  }

def _fake_urssaf(pk: int):
  # Exemple trimestriel : T1..T4 ou mensuel selon ton besoin
  periods = [
    {"label": "T1 2025", "turnover_cents": 1500000, "expenses_cents": 200000, "rate_pct": 22.0},
    {"label": "T2 2025", "turnover_cents": 1200000, "expenses_cents": 150000, "rate_pct": 22.0},
    {"label": "T3 2025", "turnover_cents": 1750000, "expenses_cents": 180000, "rate_pct": 22.0},
    {"label": "T4 2025", "turnover_cents": 1100000, "expenses_cents": 130000, "rate_pct": 22.0},
  ]
  return {
    "title": "Récapitulatif URSSAF 2025",
    "company": {"name": "CapTech", "siret": "123 456 789 00012"},
    "periods": periods,
    "note": "Taux indicatif pour micro-BNC. Vérifier votre régime exact.",
  }

# === Build context: facture / devis (mêmes règles de calcul) ===
def _build_lines_totals(rows):
  items_ctx = []
  subtotal_ht = Decimal("0")
  vat_total = Decimal("0")

  for it in rows:
    qty = Decimal(it.get("quantity", 0))
    unit_ht = cents_to_money(int(it.get("unit_price_cents", 0)))
    base_ht = money(unit_ht * qty)
    discount_pct = Decimal(it.get("discount_pct", 0)) / D100
    discount_ht = money(base_ht * discount_pct)
    line_ht = money(base_ht - discount_ht)
    vat_rate = Decimal(it.get("vat_rate", 0)) / D100
    vat_amt = money(line_ht * vat_rate)

    items_ctx.append({
      "description": it.get("description", ""),
      "quantity": qty,
      "unit_ht": unit_ht,
      "vat_rate": (vat_rate * D100),   # pour affichage en %
      "discount_pct": (discount_pct * D100),
      "base_ht": base_ht,
      "discount_ht": discount_ht,
      "line_ht": line_ht,
      "vat_amt": vat_amt,
    })

    subtotal_ht += line_ht
    vat_total += vat_amt

  total_ttc = money(subtotal_ht + vat_total)
  return items_ctx, money(subtotal_ht), money(vat_total), total_ttc

def build_invoice_context(raw):
  items, sub_ht, vat, ttc = _build_lines_totals(raw["items"])
  return {
    "q": {
      **{k: v for k, v in raw.items() if k != "items"},
      "items": items,
      "subtotal_ht": sub_ht,
      "vat_total": vat,
      "total_ttc": ttc,
    }
  }

def build_quote_context(raw):
  items, sub_ht, vat, ttc = _build_lines_totals(raw["items"])
  return {
    "q": {
      **{k: v for k, v in raw.items() if k != "items"},
      "items": items,
      "subtotal_ht": sub_ht,
      "vat_total": vat,
      "total_ttc": ttc,
    }
  }

# === Build context: URSSAF ===
def build_urssaf_context(raw):
  rows_ctx = []
  total_turnover = Decimal("0")
  total_contrib = Decimal("0")

  for p in raw["periods"]:
    turnover = cents_to_money(int(p.get("turnover_cents", 0)))
    expenses = cents_to_money(int(p.get("expenses_cents", 0)))
    taxable = money(turnover - expenses if turnover > expenses else turnover)  # simplif micro: frais non déductibles, ajuste selon régime
    rate = Decimal(p.get("rate_pct", 0)) / D100
    contrib = money(taxable * rate)

    rows_ctx.append({
      "label": p.get("label", ""),
      "turnover": turnover,
      "expenses": expenses,
      "taxable": taxable,
      "rate_pct": rate * D100,
      "contrib": contrib,
    })
    total_turnover += turnover
    total_contrib += contrib

  return {
    "r": {
      "title": raw.get("title", "Récapitulatif URSSAF"),
      "company": raw.get("company", {}),
      "rows": rows_ctx,
      "total_turnover": money(total_turnover),
      "total_contrib": money(total_contrib),
      "note": raw.get("note", ""),
    }
  }

# === Rendu PDF générique ===
def render_pdf(template_name: str, context: dict, filename: str) -> HttpResponse:
  template = get_template(template_name)
  html = template.render(context)
  resp = HttpResponse(content_type="application/pdf")
  resp["Content-Disposition"] = f'inline; filename="{filename}"'
  pisa_status = pisa.CreatePDF(html, dest=resp, link_callback=link_callback, encoding="utf-8")
  if pisa_status.err:
    return HttpResponse("Erreur génération PDF", status=500)
  return resp

# === Vues ===
def invoice_pdf(request, pk: int):
  raw = _fake_invoice(pk)  # remplace par tes modèles
  ctx = build_invoice_context(raw)
  return render_pdf("pdf/invoice.html", ctx, f"facture_{pk}.pdf")

def quote_pdf(request, pk: int):
  raw = _fake_quote(pk)    # remplace par tes modèles
  ctx = build_quote_context(raw)
  return render_pdf("pdf/quote.html", ctx, f"devis_{pk}.pdf")

def urssaf_pdf(request, pk: int):
  raw = _fake_urssaf(pk)   # remplace par tes données (mois/trimestres)
  ctx = build_urssaf_context(raw)
  return render_pdf("pdf/urssaf_summary.html", ctx, f"urssaf_{pk}.pdf")
