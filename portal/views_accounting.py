# portal/views_accounting.py
from decimal import ROUND_HALF_UP, Decimal

from django.http import HttpResponse
from django.shortcuts import render
from django.utils.dateparse import parse_date

from core.models import Customer, Invoice

from .views import _user_company  # réutilise l'utilitaire existant dans portal/views.py

Q2 = Decimal("0.01")


def cents_to_decimal(cents):
    """Convertit un montant en centimes (int/Decimal/None) en Decimal euros, arrondi à 2 décimales."""
    if cents is None:
        return Decimal("0.00")
    return (Decimal(cents) / Decimal(100)).quantize(Q2, rounding=ROUND_HALF_UP)


def accounting_dashboard(request):
    """
    Vue pour la page Comptabilité.
    - filtres GET : start_date, end_date, client (id), type (invoice/paiement not implemented here)
    - export CSV : ?export=csv
    """
    company = _user_company(request)
    if not company:
        return render(request, "portal/accounting/dashboard.html", {"company": None})

    qs = Invoice.objects.filter(company=company).select_related("customer")

    # Filtres
    start = request.GET.get("start_date")
    end = request.GET.get("end_date")
    client = request.GET.get("client")
    client_filter = None
    if start:
        d = parse_date(start)
        if d:
            qs = qs.filter(issue_date__gte=d)
    if end:
        d = parse_date(end)
        if d:
            qs = qs.filter(issue_date__lte=d)
    if client:
        try:
            client_filter = int(client)
            qs = qs.filter(customer__id=client_filter)
        except (ValueError, TypeError):
            client_filter = None

    # On limite l'affichage pour éviter surcharges (pager simple)
    page = int(request.GET.get("page") or "1")
    page_size = 50
    offset = (page - 1) * page_size
    invoices_page = list(qs.order_by("-issue_date")[offset : offset + page_size])

    # Calculs totaux : on parcourt les factures et leurs lignes pour garantir arrondis corrects
    subtotal = Decimal("0.00")
    vat_total = Decimal("0.00")

    # Précharger les lignes
    qs_with_lines = Invoice.objects.filter(
        pk__in=[i.pk for i in invoices_page]
    ).prefetch_related("items")

    invoices_map = {i.pk: i for i in invoices_page}
    for inv in qs_with_lines:
        inv_sub = Decimal("0.00")
        inv_vat = Decimal("0.00")
        for line in inv.items.all():
            unit_ht = (Decimal(line.unit_price_cents) / Decimal(100)).quantize(
                Q2, rounding=ROUND_HALF_UP
            )
            qty = Decimal(line.quantity)
            base_ht = (unit_ht * qty).quantize(Q2, rounding=ROUND_HALF_UP)
            discount_pct = Decimal(line.discount_pct or 0) / Decimal(100)
            discount_ht = (base_ht * discount_pct).quantize(Q2, rounding=ROUND_HALF_UP)
            line_ht = (base_ht - discount_ht).quantize(Q2, rounding=ROUND_HALF_UP)
            vat_amt = (line_ht * (Decimal(line.vat_rate or 0) / Decimal(100))).quantize(
                Q2, rounding=ROUND_HALF_UP
            )

            inv_sub += line_ht
            inv_vat += vat_amt
        # Attacher attributs utiles au template
        if inv.pk in invoices_map:
            invoices_map[inv.pk].total_ht = inv_sub
            invoices_map[inv.pk].total_vat = inv_vat
            invoices_map[inv.pk].total_ttc = (inv_sub + inv_vat).quantize(
                Q2, rounding=ROUND_HALF_UP
            )

        subtotal += inv_sub
        vat_total += inv_vat

    total_ttc = (subtotal + vat_total).quantize(Q2, rounding=ROUND_HALF_UP)

    # Export CSV
    if request.GET.get("export") == "csv":
        filename = "accounting_export.csv"
        response = HttpResponse(content_type="text/csv; charset=utf-8")
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        # BOM for Excel (optional)
        response.write("\ufeff")
        import csv

        writer = csv.writer(response)
        writer.writerow(
            [
                "Invoice",
                "Date",
                "Customer",
                "Status",
                "Total HT (€)",
                "TVA (€)",
                "Total TTC (€)",
            ]
        )
        full_qs = (
            Invoice.objects.filter(company=company)
            .select_related("customer")
            .prefetch_related("items")
            .order_by("-issue_date")
        )
        for inv in full_qs:
            inv_sub = Decimal("0.00")
            inv_vat = Decimal("0.00")
            for line in inv.items.all():
                unit_ht = (Decimal(line.unit_price_cents) / Decimal(100)).quantize(
                    Q2, rounding=ROUND_HALF_UP
                )
                qty = Decimal(line.quantity)
                base_ht = (unit_ht * qty).quantize(Q2, rounding=ROUND_HALF_UP)
                discount_pct = Decimal(line.discount_pct or 0) / Decimal(100)
                discount_ht = (base_ht * discount_pct).quantize(
                    Q2, rounding=ROUND_HALF_UP
                )
                line_ht = (base_ht - discount_ht).quantize(Q2, rounding=ROUND_HALF_UP)
                vat_amt = (
                    line_ht * (Decimal(line.vat_rate or 0) / Decimal(100))
                ).quantize(Q2, rounding=ROUND_HALF_UP)

                inv_sub += line_ht
                inv_vat += vat_amt

            writer.writerow(
                [
                    inv.number,
                    inv.issue_date.isoformat() if inv.issue_date else "",
                    inv.customer.name if inv.customer else "",
                    inv.status,
                    f"{inv_sub:.2f}",
                    f"{inv_vat:.2f}",
                    f"{(inv_sub + inv_vat):.2f}",
                ]
            )
        return response

    # Pour la liste de clients dans le filtre
    clients = Customer.objects.filter(company=company).order_by("name")

    ctx = {
        "company": company,
        "year": (request.GET.get("year") or ""),
        "ca_ytd": "",  # conservé par ton template (calculs existants)
        "micro_cap": "",
        "micro_progress": 0,
        "vat_base": "",
        "vat_tol": "",
        "period_start": "",
        "period_end": "",
        "urssaf_rate_label": "",
        "contrib": "",
        "invoices": invoices_page,
        "subtotal": subtotal,
        "vat_total": vat_total,
        "total_ttc": total_ttc,
        "clients": clients,
        "start_date": start,
        "end_date": end,
        "client_filter": client_filter,
        "page": page,
    }
    return render(request, "portal/accounting/dashboard.html", ctx)
