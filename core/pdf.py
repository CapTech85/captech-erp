# core/pdf.py
import os
from decimal import Decimal
from io import BytesIO

from django.conf import settings
from django.contrib.staticfiles import finders
from django.template.loader import render_to_string
from xhtml2pdf import pisa

Q2 = Decimal("0.01")


def link_callback(uri, rel):
    """
    Résout une URI statique en chemin local pour xhtml2pdf.
    """
    static_url = settings.STATIC_URL or "static/"
    if not static_url.endswith("/"):
        static_url += "/"

    # Si URI absolue (http:// or https://), on garde la partie après le domaine
    for prefix in ("http://", "https://"):
        if uri.startswith(prefix):
            uri = "/" + uri.split("/", 3)[-1]
            break

    uri_cmp = uri if uri.startswith("/") else "/" + uri
    static_cmp = static_url if static_url.startswith("/") else "/" + static_url

    if uri_cmp.startswith(static_cmp):
        subpath = uri_cmp[len(static_cmp) :]
        result = finders.find(subpath)
        if result:
            if isinstance(result, (list, tuple)):
                for p in result:
                    if os.path.isfile(p):
                        return p
            elif os.path.isfile(result):
                return result

    # Pas trouvé : renvoyer l'URI tel quel
    return uri


def render_pdf_from_template(template_name: str, context: dict) -> bytes:
    """
    Rend un template en HTML puis convertit en PDF (bytes) en utilisant xhtml2pdf.
    Passe link_callback pour résoudre correctement les assets statiques.
    """
    html = render_to_string(template_name, context)
    result = BytesIO()
    pisa_status = pisa.CreatePDF(
        html, dest=result, encoding="utf-8", link_callback=link_callback
    )

    # Si erreur de génération, on lève une exception contrôlée (utile pour debug)
    if getattr(pisa_status, "err", False):
        raise RuntimeError("Erreur lors de la génération PDF (xhtml2pdf).")

    return result.getvalue()
