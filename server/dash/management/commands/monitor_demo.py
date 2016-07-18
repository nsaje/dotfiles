import influx
import json
import logging
import time
import urllib2

from django.conf import settings

from utils import request_signer
from utils.command_helpers import ExceptionCommand

logger = logging.getLogger(__name__)

NUM_RETRIES = 10


class Command(ExceptionCommand):

    def handle(self, *args, **options):
        demo = self._start_demo()
        self._check_demo_url(demo['url'])
        self._stop_demo(demo['name'])
        influx.incr('demo.monitor', 1)

    def _start_demo(self):
        request = urllib2.Request(settings.DK_DEMO_UP_ENDPOINT)
        response = request_signer.urllib2_secure_open(request, settings.DK_API_KEY)

        status_code = response.getcode()
        if status_code != 200:
            raise Exception('Invalid response status code. status code: {}'.format(status_code))

        ret = json.loads(response.read())
        if ret['status'] != 'success':
            raise Exception('Request not successful. status: {}'.format(ret['status']))

        return {
            'name': ret.get('instance_name'),
            'url': ret.get('instance_url'),
        }

    def _check_demo_url(self, url):
        error = None
        for _ in range(NUM_RETRIES):
            try:
                response = urllib2.urlopen(url)
                body = response.read()
                if 'Zemanta One' not in body or 'Sign in' not in body:
                    raise Exception('Invalid response from demo')
                return
            except Exception as err:
                error = err
                time.sleep(5)
        raise error

    def _stop_demo(self, name):
        url = settings.DK_DEMO_DOWN_ENDPOINT.format(instance=name)
        request = urllib2.Request(url)
        response = request_signer.urllib2_secure_open(request, settings.DK_API_KEY)

        status_code = response.getcode()
        if status_code != 200:
            raise Exception('Invalid response status code. status code: {}'.format(status_code))

        ret = json.loads(response.read())
        if ret['status'] != 'pending':
            raise Exception('Request not successful. status: {}'.format(ret['status']))
