from django.apps import AppConfig
from django.conf import settings


class AutomationAppConfig(AppConfig):
    name = 'automation'

    def ready(self):
        if not settings.DISABLE_SIGNALS:
            import automation.campaignstop.signals  # noqa
            automation.campaignstop.signals.connect_notify_budgets()
            automation.campaignstop.signals.connect_notify_ad_group_settings_change()
            automation.campaignstop.signals.connect_notify_ad_group_source_settings_change()
