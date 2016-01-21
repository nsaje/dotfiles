import os
import time
import hmac
import hashlib
import requests

from django.core.management.base import BaseCommand
from django.conf import settings
from django.core.urlresolvers import reverse

from optparse import make_option
from utils.command_helpers import ExceptionCommand


class Command(ExceptionCommand):
    args = '<filepath>'
    help = 'Sends a fake mailgun request to convapi.'

    TOKEN = 'abc'
    option_list = BaseCommand.option_list + (
        make_option(
            '--hostname',
            dest='hostname',
            default='http://localhost:8000',
            help='Server hostname'),
    )

    def handle(self, *args, **options):
        if len(args) < 1:
            self.stdout.write('Missing arguments')

        filepath = args[0]
        hostname = options['hostname']

        self._fake_mailgun_request(filepath, hostname)

    def _fake_mailgun_request(self, filepath, hostname):
        timestamp = str(int(time.time()))

        signature = hmac.new(
            key=settings.MAILGUN_API_KEY,
            msg='{}{}'.format(timestamp, self.TOKEN),
            digestmod=hashlib.sha256
        ).hexdigest()

        post_data = {
            'sender': 'test@example.com',
            'recipient': 'gareports@mailapi.zemanta.com',
            'from': 'test@example.com',
            'subject': 'Test Report',
            'attachment-count': '1',
            'Date': '2014-01-12',
            'timestamp': timestamp,
            'token': self.TOKEN,
            'signature': signature
        }
        files = {
            'attachment-1': (
                os.path.split(filepath)[1],
                open(filepath),
                'text/csv',
            )
        }

        path = reverse('convapi.mailgun')

        response = requests.post(
            hostname + path,
            data=post_data,
            files=files
        )

        self.stdout.write('API returned status code {}'.format(response.status_code))
