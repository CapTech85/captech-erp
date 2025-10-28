from django.apps import AppConfig
class PortalConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "portal"

    def ready(self):
        # import des signals pour les enregistrer
        # l'import doit être local pour éviter les problèmes au moment du chargement des apps
        import portal.signals  # noqa: F401
