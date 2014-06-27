import json
import logging
import urllib2

from django.conf import settings

from actionlog import constants as actionlogconstants

logger = logging.getLogger(__name__)


def send(action):
    data = json.dumps(action.payload)
    request = urllib2.Request(settings.ZWEI_API_URL, data)

    try:
        urllib2.urlopen(request)
    except urllib2.HTTPError as e:
        logger.error('Zwei host connection error: %s', str(e))
        action.action_status = actionlogconstants.ActionStatus.FAILED
        action.save()
