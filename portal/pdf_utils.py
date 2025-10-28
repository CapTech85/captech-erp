# portal/pdf_utils.py
import os

from django.conf import settings
from django.contrib.staticfiles import finders


def link_callback(uri, rel):
    """
    Convertit une URL statique Django (avec ou sans slash initial, absolue ou relative)
    en chemin de fichier local que xhtml2pdf peut lire.
    """
    static_url = settings.STATIC_URL  # ex: "static/" ou "/static/"
    # normalise pour couvrir: "static/...", "/static/...", "http://.../static/..."
    if not static_url.endswith("/"):
        static_url += "/"

    # Retire le domaine éventuel
    # Cas absolu: http(s)://host/.../static/xxx.css
    for prefix in ("http://", "https://"):
        if uri.startswith(prefix):
            # garde la partie après le domaine
            uri = "/" + uri.split("/", 3)[-1]  # /static/xxx.css ou static/xxx.css
            break

    # Uniformise un chemin relatif en lui ajoutant un slash de tête pour la comparaison
    uri_cmp = uri if uri.startswith("/") else "/" + uri

    static_cmp = static_url if static_url.startswith("/") else "/" + static_url
    if uri_cmp.startswith(static_cmp):
        subpath = uri_cmp[
            len(static_cmp) :
        ]  # chemin relatif à STATIC_ROOT/STATICFILES_DIRS
        result = finders.find(subpath)
        if result:
            if isinstance(result, (list, tuple)):
                for p in result:
                    if os.path.isfile(p):
                        return p
            elif os.path.isfile(result):
                return result

    # Pas un fichier statique trouvé : renvoyer tel quel (images en chemin absolu, etc.)
    return uri
