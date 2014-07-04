from zemauth.models import User

from gadjo.requestprovider.signals import get_request


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
