from zemauth.models import User
from django.db.models.signals import pre_save
from gadjo.requestprovider.signals import get_request
from dash import models as dahsmodels


def modified_by_pre_save_signal_handler(sender, instance, **kwargs):
    try:
        request = get_request()
        if not isinstance(request.user, User):
            return
        instance.modified_by = request.user
    except IndexError:
        pass


def created_by_pre_save_signal_handler(sender, instance, **kwargs):
    if instance.pk is not None:
        return

    try:
        request = get_request()
        if not isinstance(request.user, User):
            return
        instance.created_by = request.user
    except IndexError:
        pass


pre_save.connect(modified_by_pre_save_signal_handler, sender=dahsmodels.Account)
pre_save.connect(modified_by_pre_save_signal_handler, sender=dahsmodels.Campaign)
pre_save.connect(modified_by_pre_save_signal_handler, sender=dahsmodels.AdGroup)
pre_save.connect(created_by_pre_save_signal_handler, sender=dahsmodels.AdGroupSettings)
pre_save.connect(created_by_pre_save_signal_handler, sender=dahsmodels.AdGroupNetworkSettings)
