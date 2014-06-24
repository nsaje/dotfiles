from django.db.models.signals import pre_save
from dash import models as dahsmodels
from gadjo.requestprovider.signals import get_request


def modified_by_pre_save_signal_handler(sender, instance, **kwargs):
    try:
        request = get_request()
        instance.modified_by = request.user
    except IndexError:
        instance.modified_by = None


def created_by_pre_save_signal_handler(sender, instance, **kwargs):
    try:
        if instance.pk is None:
            request = get_request()
            instance.created_by = request.user
    except IndexError:
        instance.created_by = None


pre_save.connect(modified_by_pre_save_signal_handler, sender=dahsmodels.ActionLog)
pre_save.connect(created_by_pre_save_signal_handler, sender=dahsmodels.ActionLog)
