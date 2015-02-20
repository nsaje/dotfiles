import logging
import sys
import traceback
import urlparse

from django.conf import settings
from django.core.urlresolvers import reverse
from django.db import transaction

import actionlog.api
import actionlog.constants
import actionlog.models
import dash.constants
import dash.models

logger = logging.getLogger(__name__)


def _init_get_content_ad_status_action(content_ad_source):
    pass


def _init_insert_content_ad_action(content_ad_source):
    pass


def _init_update_content_ad_action(content_ad_sources):
    pass


def _create_action(content_ad_source, action, args={}):
    ad_group_source = dash.models.AdGroupSource.objects.get(
        ad_group_id=content_ad_source.content_ad.ad_group,
        source=content_ad_source.source,
    )

    action = actionlog.models.ActionLog.objects.create(
        action=actionlog.constants.GET_CONTENT_AD_STATUS,
        action_type=actionlog.constants.ActionType.AUTOMATIC,
        ad_group_source=ad_group_source,
    )

    try:
        with transaction.atomic():
            callback = urlparse.urljoin(
                settings.EINS_HOST, reverse('api.zwei_callback', kwargs={'action_id': action.id})
            )

            args.update({
                'content_ad_key': content_ad_source.get_source_key()
            })

            payload = {
                'action': action.action,
                'source': ad_group_source.source.source_type and ad_group_source.source.source_type.type,
                'expiration_dt': action.expiration_dt,
                'credentials': ad_group_source.source_credentials and ad_group_source.source_credentials.credentials,
                'args': args,
                'callback_url': callback
            }

            action.payload = payload
            action.save()

            return action
    except Exception as e:
        logger.exception('An exception occurred while initializing content ad source action.')
        msg = traceback.format_exc(e)

        action.state = actionlog.constants.ActionState.FAILED
        action.message = msg
        action.save()

        et, ei, tb = sys.exc_info()
        raise actionlog.api.InsertActionException, ei, tb
