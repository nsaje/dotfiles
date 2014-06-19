import httplib
import urllib2
import urlparse

from django.conf import settings

from . import constants


def send(action):
    url = urlparse.urljoin(settings.ZWEI_API_HOST, 'task')
    request = urllib2.Request(url, action.payload)
    response = urllib2.urlopen(request)

    if response.status_code != httplib.OK:
        action.status = constants.ActionStatus.ERROR
        action.save()
