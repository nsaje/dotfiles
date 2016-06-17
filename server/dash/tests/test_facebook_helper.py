import json

from django.test import TestCase, override_settings
from mock import patch
from requests import Response

from dash import facebook_helper, constants, models
from dash.facebook_helper import FB_PAGES_URL, FB_API_VERSION, FB_PAGE_ID_URL


@override_settings(
    FB_BUSINESS_ID='fake_business_id',
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
    def _get_token_json():
        return {'access_token': 'very_fake_token'}

    @staticmethod
    def _get_headers():
        return {'Content-Type': 'application/json', 'Accept': 'application/json'}

    @staticmethod
    def _get_fb_account(page_url, page_id):
        fb_account = models.FacebookAccount()
        fb_account.page_url = page_url
        fb_account.page_id = page_id
        return fb_account

    @patch('requests.get')
    @patch('requests.post')
    def test_unchanged_page(self, mock_post, mock_get):
        page_url = 'http://facebook.com/existing_page_id'
        page_id = '1234'
        fb_account = self._get_fb_account(page_url, page_id)
        facebook_helper.update_facebook_account(fb_account, page_url)

        self.assertEqual(fb_account.page_url, page_url)
        self.assertEqual(fb_account.page_id, page_id)
        self.assertFalse(mock_post.called)
        self.assertFalse(mock_get.called)

    @patch('requests.get')
    @patch('requests.post')
    def test_new_page(self, mock_request, mock_page_id):
        page_url = 'http://www.facebook.com/new_page'
        page_id = '1234'

        mock_page_id.return_value = self._create_response(200, '{"id": "1234"}')
        mock_request.return_value = self._create_response(
            200,
            '{"response":"All clear"}'
        )

        fb_account = self._get_fb_account(None, None)
        facebook_helper.update_facebook_account(fb_account, page_url)

        self.assertEqual(fb_account.page_url, page_url)
        self.assertEqual(fb_account.page_id, page_id)
        self.assertEqual(fb_account.status, constants.FacebookPageRequestType.PENDING)
        self.assertTrue(mock_page_id.called)
        self.assertTrue(mock_request.called)

    @patch('requests.get')
    @patch('requests.post')
    def test_changed_page(self, mock_request, mock_page_id):
        page_url = 'http://www.facebook.com/new_page'
        page_id = '9876'

        mock_page_id.return_value = self._create_response(200, '{"id": "9876"}')
        mock_request.return_value = self._create_response(
            200,
            '{"response":"All clear"}'
        )

        fb_account = self._get_fb_account('http://www.facebook.com/old_page', "1234")
        facebook_helper.update_facebook_account(fb_account, page_url)

        self.assertEqual(fb_account.page_url, page_url)
        self.assertEqual(fb_account.page_id, page_id)
        self.assertEqual(fb_account.status, constants.FacebookPageRequestType.PENDING)
        self.assertTrue(mock_page_id.called)
        self.assertTrue(mock_request.called)

    @patch('requests.get')
    @patch('requests.post')
    def test_clear_page(self, mock_request, mock_page_id):
        page_url = 'http://facebook.com/existing_page'
        page_id = '1234'
        fb_account = self._get_fb_account(page_url, page_id)
        facebook_helper.update_facebook_account(fb_account, None)

        self.assertEqual(fb_account.page_url, None)
        self.assertEqual(fb_account.page_id, None)
        self.assertEqual(fb_account.status, constants.FacebookPageRequestType.EMPTY)
        self.assertFalse(mock_request.called)
        self.assertFalse(mock_page_id.called)

    @patch('requests.get')
    def test_valid_page_id(self, mock_get):
        page_url = 'http://fb.com/page_name'

        mock_get.return_value = self._create_response(200, '{"id": "1234", "some_other_stuff": "i don\'t care about"}')

        page_id = facebook_helper.get_page_id(page_url)

        mock_get.assert_called_once_with(FB_PAGE_ID_URL.format(FB_API_VERSION, 'page_name'),
                                         params=self._get_token_json())
        self.assertEqual(page_id, "1234")

    @patch('requests.get')
    def test_invalid_page_id(self, mock_get):
        page_url = 'http://fb.com/invalid_page'

        mock_get.return_value = self._create_response(400, '{"error": "Go away with this page"}')

        page_id = facebook_helper.get_page_id(page_url)

        mock_get.assert_called_once_with(FB_PAGE_ID_URL.format(FB_API_VERSION, 'invalid_page'),
                                         params=self._get_token_json())
        self.assertEqual(page_id, None)

    def test_extract_page_id_from_url(self):
        expected_page_id = '1234'

        page_url = 'http://fb.com/dummy-dummy-1234'
        page_id = facebook_helper._extract_page_id_from_url(page_url)
        self.assertEqual(page_id, expected_page_id)

        page_url = 'http://fb.com/dummy-1234/'
        page_id = facebook_helper._extract_page_id_from_url(page_url)
        self.assertEqual(page_id, expected_page_id)

        page_url = '/dummy----1234/'
        page_id = facebook_helper._extract_page_id_from_url(page_url)
        self.assertEqual(page_id, expected_page_id)

        page_url = '/1234'
        page_id = facebook_helper._extract_page_id_from_url(page_url)
        self.assertEqual(page_id, expected_page_id)

        page_url = '1234/'
        page_id = facebook_helper._extract_page_id_from_url(page_url)
        self.assertEqual(page_id, expected_page_id)

        page_url = '1234'
        page_id = facebook_helper._extract_page_id_from_url(page_url)
        self.assertEqual(page_id, expected_page_id)

    @patch('requests.post')
    def test_invalid_page(self, mock_post):
        mock_post.return_value = self._create_response(
            400,
            '{"error":{"message": "Code: (#100) Param page_id must be a valid page ID not your fake page id"}}',
        )

        page_id = 'invalid_page_id'
        status = facebook_helper._send_page_access_request(page_id)

        mock_post.assert_called_once_with(FB_PAGES_URL.format(FB_API_VERSION, 'fake_business_id'),
                                          data=json.dumps(self._get_params(page_id)), headers=self._get_headers())
        self.assertEqual(status, constants.FacebookPageRequestType.INVALID)

    @patch('requests.post')
    def test_already_pending(self, mock):
        mock.return_value = self._create_response(
            400,
            '{"error":{"message": "Code: (#100) There is already pending client request for page pending_page_id"}}'
        )

        page_id = 'pending_page_id'
        status = facebook_helper._send_page_access_request(page_id)

        mock.assert_called_once_with(FB_PAGES_URL.format(FB_API_VERSION, 'fake_business_id'),
                                     data=json.dumps(self._get_params(page_id)), headers=self._get_headers())
        self.assertEqual(status, constants.FacebookPageRequestType.PENDING)

    @patch('requests.post')
    def test_already_connected(self, mock):
        mock.return_value = self._create_response(
            400,
            '{"error":{"error_user_title": "Code: (#100) You Already Have Access To This Page"}}'
        )

        page_id = 'pending_page_id'
        status = facebook_helper._send_page_access_request(page_id)

        mock.assert_called_once_with(FB_PAGES_URL.format(FB_API_VERSION, 'fake_business_id'),
                                     data=json.dumps(self._get_params(page_id)), headers=self._get_headers())
        self.assertEqual(status, constants.FacebookPageRequestType.CONNECTED)

    @patch('requests.post')
    def test_approval_sent_successfully(self, mock):
        mock.return_value = self._create_response(
            200,
            '{"dummy":{"dummy": "dummy"}}'
        )

        page_id = 'approve_me_page'
        status = facebook_helper._send_page_access_request(page_id)

        mock.assert_called_once_with(FB_PAGES_URL.format(FB_API_VERSION, 'fake_business_id'),
                                     data=json.dumps(self._get_params(page_id)), headers=self._get_headers())
        self.assertEqual(status, constants.FacebookPageRequestType.PENDING)

    @patch('requests.post')
    def test_unknown_error(self, mock):
        mock.return_value = self._create_response(
            500,
            '{"dummy":{"dummy": "dummy"}}'
        )

        page_id = 'approve_me_page'
        status = facebook_helper._send_page_access_request(page_id)

        mock.assert_called_once_with(FB_PAGES_URL.format(FB_API_VERSION, 'fake_business_id'),
                                     data=json.dumps(self._get_params(page_id)), headers=self._get_headers())
        self.assertEqual(status, constants.FacebookPageRequestType.ERROR)
