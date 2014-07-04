from django.db.models.signals import pre_save

from utils import signal_handlers

from dash import models as dahsmodels


pre_save.connect(signal_handlers.modified_by_pre_save_signal_handler, sender=dahsmodels.Account)
pre_save.connect(signal_handlers.modified_by_pre_save_signal_handler, sender=dahsmodels.Campaign)
pre_save.connect(signal_handlers.modified_by_pre_save_signal_handler, sender=dahsmodels.AdGroup)
pre_save.connect(signal_handlers.created_by_pre_save_signal_handler, sender=dahsmodels.AdGroupSettings)
pre_save.connect(signal_handlers.created_by_pre_save_signal_handler, sender=dahsmodels.AdGroupNetworkSettings)
