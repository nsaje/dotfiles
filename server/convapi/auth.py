
import hmac
import hashlib

from django.conf import settings


class GASourceAuth(object):

    def __init__(self, email):
        self.email = email

    def is_authorised(self):
        return True


class MailGunRequestAuth(object):

    def __init__(self, request):
        self.request = request

    def is_authorised(self):

        timestamp = self.request.POST['timestamp']
        # take only int part
        timestamp = int(float(timestamp))

        signature = self.request.POST['signature']
        token = self.request.POST['token']

        expected_signature = hmac.new(
            key=settings.MAILGUN_API_KEY,
            msg='{}{}'.format(timestamp, token),
            digestmod=hashlib.sha256
        ).hexdigest()

        return signature == expected_signature
