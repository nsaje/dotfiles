from django.db.models.signals import pre_save
from gadjo.requestprovider.signals import get_request
from dash import models as dahsmodels


def changed_by_pre_save_signal_handler(sender, instance, **kwargs):
	request = get_request()
	instance.changed_by = request.user

pre_save.connect(changed_by_pre_save_signal_handler, sender=dahsmodels.Account)	
pre_save.connect(changed_by_pre_save_signal_handler, sender=dahsmodels.Campaign)
pre_save.connect(changed_by_pre_save_signal_handler, sender=dahsmodels.AdGroup)