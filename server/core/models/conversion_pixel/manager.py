from django.db import transaction

import core.common
import dash.constants
import utils.email_helper
import utils.k1_helper
import utils.redirector

from . import model


class ConversionPixelManager(core.common.BaseManager):
    @transaction.atomic
    def create(self, request, account, skip_notification=False, **settings):
        core.common.entity_limits.enforce(
            model.ConversionPixel.objects.filter(account=account, archived=False), account.id
        )
        pixel = model.ConversionPixel(
            account=account, slug=model.ConversionPixel._SLUG_PLACEHOLDER, redirect_url="", notes=""
        )
        pixel.update(request, skip_propagation=True, **settings)
        utils.redirector.update_pixel(pixel)

        changes_text = "Created a conversion pixel named {}.".format(pixel.name)
        action_type = dash.constants.HistoryActionType.CONVERSION_PIXEL_CREATE

        account.write_history(changes_text, user=request.user if request else None, action_type=action_type)

        if not skip_notification:
            utils.email_helper.send_account_pixel_notification(account, request)

        return pixel
