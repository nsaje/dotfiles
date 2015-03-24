from django.db.models.signals import pre_save

from utils import signal_handlers

from actionlog import models


pre_save.connect(signal_handlers.trigger_alert_pre_save_signal_handler, sender=models.ActionLog)
