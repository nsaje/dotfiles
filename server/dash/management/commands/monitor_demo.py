import influx
import json
import logging
import time
import urllib2
import requests

from django.conf import settings

from utils import request_signer
from utils.command_helpers import ExceptionCommand

logger = logging.getLogger(__name__)

NUM_RETRIES = 10


class Command(ExceptionCommand):

    def handle(self, *args, **options):
        demo = self._start_demo()
        self._check_demo_url(demo)
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
            'username': ret.get('instance_username'),
            'password': ret.get('instance_password'),
        }

    def _find_string_in_login_page(session):
        response = session.get(url)
        body = response.text
        csrf_token = session.cookies['csrftoken']
        if 'Zemanta One' not in body or 'Sign in' not in body:
            raise Exception('Invalid response from demo')
        return session

    def _try_to_login(session, demo_instance):
        response = session.post(
            url='%s/signin' % url,
            data={
                'username': demo_instance['username'],
                'password': demo_instance['password'],
                'csrfmiddlewaretoken': csrf_token
                },
            headers={'Referer': '%s/signin?next=/' % demo_instance['url']}
        )
        if response.status_code != 200:
            raise Exception('Invalid response code from demo signin')
        return session

    def _fetch_all_accounts_nav(session, demo_instance):
        response = session.get(
            url='%s/api/all_accounts/nav/' % demo_instance['url'], headers={'Accept': 'application/json', }
        )
        if response.status_code != 200:
            raise Exception('Invalid response code from demo nav')
        data = json.loads(response.text)
        if not data.get('success', False):
            raise Exception("Couldn't get basic nav data")
        return session

    def _check_demo_url(self, demo_instance):
        error = Exception("Automatic 'Request demoV3' check failed for unknown reason.")
        for _ in range(NUM_RETRIES):
            try:
                session = requests.Session()
                _find_string_in_login_page(session)
                _try_to_login(session, demo_instance)
                _fetch_all_accounts_nav(session, demo_instance)
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
