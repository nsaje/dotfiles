import json

from mock import patch, Mock

from django.test import TestCase, override_settings
from django.conf import settings

from utils import redirector_helper


@override_settings(
    R1_API_SIGN_KEY='AAAAAAAAAAAAAAAAAAAAAAAA',
    R1_VALIDATE_API_URL='https://r1.zemanta.com/api/validate/',
)
@patch('utils.request_signer._secure_opener.open')
class ValidateURLTest(TestCase):
    def test_validate_url(self, mock_urlopen):
        url = "https://example.com"

        response = Mock()
        response.read.return_value = json.dumps({"data": True, "status": "ok"})
        response.getcode = lambda: 200
        mock_urlopen.return_value = response

        self.assertEqual(redirector_helper.validate_url(url, 1), True)

        call = mock_urlopen.call_args[0][0]

        self.assertEqual(call.get_full_url(), settings.R1_VALIDATE_API_URL)
        self.assertEqual(call.data, json.dumps({"url": url, "adgroupid": 1}))

    def test_code_error(self, mock_urlopen):
        url = 'https://example.com/image'

        response = Mock()
        response.getcode = lambda: 500
        mock_urlopen.return_value = response

        with self.assertRaises(Exception):
            redirector_helper.validate_url(url, 1)
        self.assertEqual(len(mock_urlopen.call_args_list), 3)

    def test_status_not_success(self, mock_urlopen):
        url = 'https://example.com/image'

        response = Mock()
        response.read.return_value = '{"status": "error"}'
        response.getcode = lambda: 200
        mock_urlopen.return_value = response

        with self.assertRaises(Exception):
            redirector_helper.validate_url(url, 1)
        self.assertEqual(len(mock_urlopen.call_args_list), 3)


@override_settings(
    R1_REDIRECTS_API_URL='https://r1.example.com/api/redirects/',
    R1_REDIRECTS_ADGROUP_API_URL='https://r1.example.com/api/redirects/',
    R1_API_SIGN_KEY='AAAAAAAAAAAAAAAAAAAAAAAA'
)
@patch('utils.request_signer._secure_opener.open')
class InsertRedirectTest(TestCase):
    def test_insert_redirect(self, mock_urlopen):
        url = "https://example.com"
        content_ad_id = 123
        ad_group_id = 345

        redirect_id = "u123456"

        response = Mock()
        response.read.return_value = '{"data": "%s", "status": "ok"}' % redirect_id
        response.getcode = lambda: 200
        mock_urlopen.return_value = response

        self.assertEqual(redirector_helper.insert_redirect(url, content_ad_id, ad_group_id), redirect_id)

        call = mock_urlopen.call_args[0][0]

        self.assertEqual(call.get_full_url(), settings.R1_REDIRECTS_API_URL)
        self.assertEqual(call.data, json.dumps({"url": "https://example.com", "creativeid": content_ad_id, "adgroupid": ad_group_id}))

    def test_code_error(self, mock_urlopen):
        url = 'https://example.com/image'

        response = Mock()
        response.getcode = lambda: 500
        mock_urlopen.return_value = response

        with self.assertRaises(Exception):
            redirector_helper.insert_redirect(url, 0, 0)
        self.assertEqual(len(mock_urlopen.call_args_list), 3)

    def test_status_not_success(self, mock_urlopen):
        url = 'https://example.com/image'

        response = Mock()
        response.read.return_value = '{"status": "error"}'
        response.getcode = lambda: 200
        mock_urlopen.return_value = response

        with self.assertRaises(Exception):
            redirector_helper.insert_redirect(url, 0, 0)
        self.assertEqual(len(mock_urlopen.call_args_list), 3)


@override_settings(
    R1_REDIRECTS_API_URL='https://r1.example.com/api/redirects/',
    R1_REDIRECTS_ADGROUP_API_URL='https://r1.example.com/api/redirects/',
    R1_API_SIGN_KEY='AAAAAAAAAAAAAAAAAAAAAAAA'
)
@patch('utils.request_signer._secure_opener.open')
class InsertAdGroupTest(TestCase):
    def test_insert_adgroup(self, mock_urlopen):
        ad_group_id = 345
        tracking_codes = "lala=1"
        enable_ga_tracking = True
        enable_adobe_tracking = False
        adobe_tracking_param = 'cid'

        response = Mock()
        response.read.return_value = '{"status": "ok"}'
        response.getcode = lambda: 200
        mock_urlopen.return_value = response

        redirector_helper.insert_adgroup(
            ad_group_id,
            tracking_codes,
            enable_ga_tracking,
            enable_adobe_tracking,
            adobe_tracking_param
        )

        call = mock_urlopen.call_args[0][0]

        self.assertEqual(call.get_full_url(), settings.R1_REDIRECTS_ADGROUP_API_URL.format(adgroup=ad_group_id))
        self.assertEqual(call.data, json.dumps({
            "trackingcode": tracking_codes,
            "enablegatracking": True,
            "enableadobetracking": False,
            "adobetrackingparam": 'cid'
        }))

    def test_code_error(self, mock_urlopen):
        url = 'https://example.com/image'

        response = Mock()
        response.getcode = lambda: 500
        mock_urlopen.return_value = response

        with self.assertRaises(Exception):
            redirector_helper.insert_adgroup(url, '', True, False, '')
        self.assertEqual(len(mock_urlopen.call_args_list), 3)

    def test_status_not_success(self, mock_urlopen):
        url = 'https://example.com/image'

        response = Mock()
        response.read.return_value = '{"status": "error"}'
        response.getcode = lambda: 200
        mock_urlopen.return_value = response

        with self.assertRaises(Exception):
            redirector_helper.insert_adgroup(url, '', True, False, '')
        self.assertEqual(len(mock_urlopen.call_args_list), 3)
