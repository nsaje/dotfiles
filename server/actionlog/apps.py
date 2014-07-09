from django.apps import AppConfig


class ActionLogAppConfig(AppConfig):
    name = 'actionlog'

    def ready(self):
        import actionlog.signals
