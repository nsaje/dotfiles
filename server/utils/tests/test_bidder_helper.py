import json

from mock import patch, Mock

from django.test import TestCase, override_settings
from django.conf import settings

from utils import bidder_helper


@override_settings(
    BIDDER_API_SIGN_KEY='AAAAAAAAAAAAAAAAAAAAAAAA',
    BIDDER_API_URL_BASE='https://b1api.zemanta.com',
)
@patch('utils.request_signer._secure_opener.open')
class AdGroupSpendTest(TestCase):
    def test_adgroup_realtimespend(self, mock_urlopen):
        response = Mock()
        response.read.return_value = json.dumps({"spend": 12.3, "error": None})
        response.getcode = lambda: 200
        mock_urlopen.return_value = response

        self.assertEqual(bidder_helper.get_adgroup_realtimespend(1), {'spend': 12.3})

        call = mock_urlopen.call_args[0][0]

        self.assertEqual(call.get_full_url(), 'https://b1api.zemanta.com/api/realtimestats/1/')
