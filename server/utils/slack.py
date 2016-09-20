import json
import urllib
import urllib2

from django.conf import settings

from stats.constants import SlackMsgTypes

DEFAULT_USERNAME = 'z1'


def _post_to_slack(data):
    data = urllib.urlencode({
        'payload': json.dumps(data)
    })
    req = urllib2.Request(settings.SLACK_INCOMING_HOOK_URL, data)
    response = urllib2.urlopen(req)
    return response.read() == 'ok'


def link(url='', anchor=''):
    return '<{url}|{anchor}>'.format(url=url, anchor=anchor)


def publish(text, channel=None, msg_type=SlackMsgTypes.INFO, username=DEFAULT_USERNAME):
    data = {
        'text': text,
        'username': username,
    }
    if msg_type:
        data['icon_emoji'] = msg_type
    if channel:
        data['channel'] = channel
    _post_to_slack(data)
