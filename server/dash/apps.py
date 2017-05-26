from django.apps import AppConfig


class DashAppConfig(AppConfig):
    name = 'dash'

    def ready(self):
        import dash.signals  # noqa: F401
