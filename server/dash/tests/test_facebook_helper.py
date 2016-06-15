import json

from django.test import TestCase, override_settings
from mock import patch
from requests import Response

from dash import facebook_helper, constants, models


@override_settings(
    FB_BUSINESS_ID='fake_app_id',
    FB_ACCESS_TOKEN='very_fake_token',
)
class FacebookPageAccessTest(TestCase):

    @staticmethod
    def _create_response(status_code, content):
        response = Response()
        response.status_code = status_code
        response._content = content
        return response

    @staticmethod
    def _get_params(page_id):
        return {'page_id': page_id,
                'access_type': 'AGENCY',
                'permitted_roles': ['ADVERTISER'],
                'access_token': 'very_fake_token'}

    @staticmethod
    def _get_headers():
        return {'Content-Type': 'application/json', 'Accept': 'application/json'}

    @staticmethod
    def _get_version():
        return 'v2.6'

    @staticmethod
    def _get_fb_api_url():
        return 'https://graph.facebook.com/%s/%s/pages'

    @staticmethod
    def _get_fb_account(page_id):
        fb_account = models.FacebookAccount()
        fb_account.page_url = page_id
        return fb_account

    @patch('requests.post')
    def test_unchanged_page(self, mock):
        page_id = 'existing_page_id'
        fb_account = self._get_fb_account(page_id)
        facebook_helper.update_facebook_account(fb_account, page_id)

        self.assertEqual(fb_account.get_page_id(), page_id)
        self.assertFalse(mock.called)

    @patch('requests.post')
    def test_changed_page(self, mock):
        mock.return_value = self._create_response(
            200,
            '{"response":"All clear"}'
        )

        page_id = 'new_page_id'
        fb_account = self._get_fb_account('old_page_id')
        facebook_helper.update_facebook_account(fb_account, page_id)

        self.assertEqual(fb_account.get_page_id(), page_id)
        self.assertTrue(mock.called)

    @patch('requests.post')
    def test_clear_page(self, mock):
        page_id = 'existing_page_id'
        fb_account = self._get_fb_account(page_id)
        facebook_helper.update_facebook_account(fb_account, None)

        self.assertEqual(fb_account.get_page_id(), None)
        self.assertEqual(fb_account.status, constants.FacebookPageRequestType.EMPTY)
        self.assertFalse(mock.called)

    @patch('requests.post')
    def test_invalid_page(self, mock):
        mock.return_value = self._create_response(
            400,
            '{"error":{"message": "Code: (#100) Param page_id must be a valid page ID not your fake page id"}}'
        )

        page_id = 'invalid_page_id'
        fb_account = self._get_fb_account(page_id)
        status = facebook_helper._send_page_access_request(fb_account)

        mock.assert_called_once_with(self._get_fb_api_url() % (self._get_version(), 'fake_app_id'),
                                     data=json.dumps(self._get_params(page_id)), headers=self._get_headers())
        self.assertEqual(status, constants.FacebookPageRequestType.INVALID)

    @patch('requests.post')
    def test_already_pending(self, mock):
        mock.return_value = self._create_response(
            400,
            '{"error":{"message": "Code: (#100) There is already pending client request for page pending_page_id"}}'
        )

        page_id = 'pending_page_id'
        fb_account = self._get_fb_account(page_id)
        status = facebook_helper._send_page_access_request(fb_account)

        mock.assert_called_once_with(self._get_fb_api_url() % (self._get_version(), 'fake_app_id'),
                                     data=json.dumps(self._get_params(page_id)), headers=self._get_headers())
        self.assertEqual(status, constants.FacebookPageRequestType.PENDING)

    @patch('requests.post')
    def test_already_connected(self, mock):
        mock.return_value = self._create_response(
            400,
            '{"error":{"error_user_title": "Code: (#100) You Already Have Access To This Page"}}'
        )

        page_id = 'pending_page_id'
        fb_account = self._get_fb_account(page_id)
        status = facebook_helper._send_page_access_request(fb_account)

        mock.assert_called_once_with(self._get_fb_api_url() % (self._get_version(), 'fake_app_id'),
                                     data=json.dumps(self._get_params(page_id)), headers=self._get_headers())
        self.assertEqual(status, constants.FacebookPageRequestType.CONNECTED)

    @patch('requests.post')
    def test_approval_sent_successfully(self, mock):
        mock.return_value = self._create_response(
            200,
            '{"dummy":{"dummy": "dummy"}}'
        )

        page_id = 'approve_me_page'
        fb_account = self._get_fb_account(page_id)
        status = facebook_helper._send_page_access_request(fb_account)

        mock.assert_called_once_with(self._get_fb_api_url() % (self._get_version(), 'fake_app_id'),
                                     data=json.dumps(self._get_params(page_id)), headers=self._get_headers())
        self.assertEqual(status, constants.FacebookPageRequestType.PENDING)

    @patch('requests.post')
    def test_unknown_error(self, mock):
        mock.return_value = self._create_response(
            500,
            '{"dummy":{"dummy": "dummy"}}'
        )

        page_id = 'approve_me_page'
        fb_account = self._get_fb_account(page_id)
        status = facebook_helper._send_page_access_request(fb_account)

        mock.assert_called_once_with(self._get_fb_api_url() % (self._get_version(), 'fake_app_id'),
                                     data=json.dumps(self._get_params(page_id)), headers=self._get_headers())
        self.assertEqual(status, constants.FacebookPageRequestType.ERROR)
