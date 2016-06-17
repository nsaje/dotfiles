from django.core.management import CommandError
from django.test import TransactionTestCase, override_settings
from mock import patch
from raven.utils import json
from requests import Response

from dash.management.commands import check_facebook_page_approval
from dash.management.commands.check_facebook_page_approval import FB_AD_ACCOUNT_URL, FB_API_VERSION, CURRENCY_USD, \
    TZ_AMERICA_NEW_YORK, FB_USER_PERMISSIONS_URL


@override_settings(
    FB_BUSINESS_ID='fake_business_id',
    FB_ACCESS_TOKEN='very_fake_token',
    FB_APP_ID='very_fake_app_id',
    FB_SYSTEM_USER_ID='fake_system_user_id'
)
class CheckFacebookPageApprovalTest(TransactionTestCase):
    @staticmethod
    def _create_response(status_code, content):
        response = Response()
        response.status_code = status_code
        response._content = content
        return response

    @staticmethod
    def _get_headers():
        return {'Content-Type': 'application/json', 'Accept': 'application/json'}

    @staticmethod
    def _get_account_params(name, page_id):
        return {'name': name,
                'currency': CURRENCY_USD,
                'timezone_id': TZ_AMERICA_NEW_YORK,
                'end_advertiser': page_id,
                'media_agency': 'very_fake_app_id',
                'partner': page_id,
                'access_token': 'very_fake_token'}

    @staticmethod
    def _get_user_params(role):
        return {'business': 'fake_business_id',
                'user': 'fake_system_user_id',
                'role': role,
                'access_token': 'very_fake_token'}

    def test_command(self):
        pass

    @patch('requests.get')
    def test_get_all_pages(self, mock):
        response = {
            "data": [{"id": "first", "access_status": "connected"},
                     {"id": "second", "access_status": "pending"},
                     {"id": "third", "access_status": "unknown"}
                     ]}
        mock.return_value = self._create_response(200, json.dumps(response))

        pages_dict = check_facebook_page_approval._get_all_pages()

        expected = {'first': 'connected', 'second': 'pending', 'third': 'unknown'}
        self.assertEqual(pages_dict, expected)

    @patch('requests.get')
    def test_get_all_pages_error(self, mock):
        response = {
            "error": "invalid request"}
        mock.return_value = self._create_response(500, json.dumps(response))

        self.assertRaises(CommandError, check_facebook_page_approval._get_all_pages)

    @patch('requests.post')
    def test_create_ad_account(self, mock):
        mock.return_value = self._create_response(200, '{"id": "1000"}')
        name = 'dummy_name'
        page_id = '1234'

        ad_account_id = check_facebook_page_approval._create_ad_account(name, page_id)

        mock.assert_called_once_with(FB_AD_ACCOUNT_URL.format(FB_API_VERSION, 'fake_business_id'),
                                     json.dumps(self._get_account_params(name, page_id)), headers=self._get_headers())
        self.assertEqual("1000", ad_account_id)

    @patch('requests.post')
    def test_create_ad_account_failed(self, mock):
        mock.return_value = self._create_response(500, '{"error": "invalid request"}')
        name = 'dummy_name'
        page_id = '1234'

        self.assertRaises(CommandError, check_facebook_page_approval._create_ad_account, name, page_id)
        mock.assert_called_once_with(FB_AD_ACCOUNT_URL.format(FB_API_VERSION, 'fake_business_id'),
                                     json.dumps(self._get_account_params(name, page_id)), headers=self._get_headers())

    @patch('requests.post')
    def test_add_system_user_to_account(self, mock):
        mock.return_value = self._create_response(200, '')

        account_id = "1000"
        check_facebook_page_approval._add_system_user_permissions(account_id, 'ADMIN')
        mock.assert_called_once_with(FB_USER_PERMISSIONS_URL.format(FB_API_VERSION, account_id),
                                     json.dumps(self._get_user_params('ADMIN')), headers=self._get_headers())

    @patch('requests.post')
    def test_add_system_user_to_account_failed(self, mock):
        mock.return_value = self._create_response(500, 'some error we don\'t care about')

        account_id = "1000"
        self.assertRaises(CommandError, check_facebook_page_approval._add_system_user_permissions, account_id, 'ADMIN')
        mock.assert_called_once_with(FB_USER_PERMISSIONS_URL.format(FB_API_VERSION, account_id),
                                     json.dumps(self._get_user_params('ADMIN')), headers=self._get_headers())

    @patch('requests.post')
    def test_add_system_user_to_page(self, mock):
        mock.return_value = self._create_response(200, '')

        page_id = "1234"
        check_facebook_page_approval._add_system_user_permissions(page_id, 'ADVERTISER')
        mock.assert_called_once_with(FB_USER_PERMISSIONS_URL.format(FB_API_VERSION, page_id),
                                     json.dumps(self._get_user_params('ADVERTISER')), headers=self._get_headers())

    @patch('requests.post')
    def test_add_system_user_to_page_failed(self, mock):
        mock.return_value = self._create_response(500, 'some error we don\'t care about')

        page_id = "1234"
        self.assertRaises(CommandError, check_facebook_page_approval._add_system_user_permissions, page_id,
                          'ADVERTISER')
        mock.assert_called_once_with(FB_USER_PERMISSIONS_URL.format(FB_API_VERSION, page_id),
                                     json.dumps(self._get_user_params('ADVERTISER')), headers=self._get_headers())
