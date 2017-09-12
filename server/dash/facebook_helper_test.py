import json

from django.test import TestCase
from mock import patch
from requests import Response

from dash import facebook_helper, constants, models
from dash.facebook_helper import FB_PAGES_URL, FB_API_VERSION, FB_PAGE_ID_URL, FB_AD_ACCOUNT_CREATE_URL, \
    FB_USER_PERMISSIONS_URL, CURRENCY_USD, TZ_AMERICA_NEW_YORK


class FacebookPageAccessTest(TestCase):
    @staticmethod
    def get_credentials():
        return {
            "app_id": "fake_app_id",
            "app_secret": "fake_app_secret",
            "access_token": "fake_access_token",
            "business_id": "fake_business_id",
            "system_user_id": "fake_system_user_id",
        }

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
                'access_token': 'fake_access_token'}

    @staticmethod
    def _get_headers():
        return {'Content-Type': 'application/json', 'Accept': 'application/json'}

    @staticmethod
    def _get_fb_account(page_url, page_id):
        fb_account = models.FacebookAccount()
        fb_account.page_url = page_url
        fb_account.page_id = page_id

        account = models.Account()
        fb_account.account = account
        return fb_account

    @patch('dash.facebook_helper.stop_facebook_media_sources')
    @patch('requests.get')
    @patch('requests.post')
    def test_update_unchanged_page(self, mock_post, mock_get, mock_stop):
        page_url = 'http://facebook.com/existing_page_id'
        page_id = '1234'
        fb_account = self._get_fb_account(page_url, page_id)
        credentials = self.get_credentials()
        facebook_helper.update_facebook_account(fb_account, page_url, credentials['business_id'],
                                                credentials['access_token'])

        self.assertEqual(fb_account.page_url, page_url)
        self.assertEqual(fb_account.page_id, page_id)
        self.assertFalse(mock_post.called)
        self.assertFalse(mock_get.called)
        self.assertFalse(mock_stop.called)

    @patch('dash.facebook_helper.stop_facebook_media_sources')
    @patch('requests.get')
    @patch('requests.post')
    def test_update_new_page(self, mock_request, mock_page_id, mock_stop):
        page_url = 'http://www.facebook.com/new_page'
        page_id = '1234'

        mock_page_id.return_value = self._create_response(200, '{"id": "1234"}')
        mock_request.return_value = self._create_response(
            200,
            '{"response":"All clear"}'
        )

        fb_account = self._get_fb_account(None, None)
        credentials = self.get_credentials()
        facebook_helper.update_facebook_account(fb_account, page_url, credentials['business_id'],
                                                credentials['access_token'])

        self.assertEqual(fb_account.page_url, page_url)
        self.assertEqual(fb_account.page_id, page_id)
        self.assertEqual(fb_account.status, constants.FacebookPageRequestType.PENDING)
        self.assertTrue(mock_page_id.called)
        self.assertTrue(mock_request.called)
        mock_stop.assert_called_once_with(fb_account.account)

    @patch('dash.facebook_helper.stop_facebook_media_sources')
    @patch('requests.get')
    @patch('requests.post')
    def test_update_changed_page(self, mock_request, mock_page_id, mock_stop):
        page_url = 'http://www.facebook.com/new_page'
        page_id = '9876'

        mock_page_id.return_value = self._create_response(200, '{"id": "9876"}')
        mock_request.return_value = self._create_response(
            200,
            '{"response":"All clear"}'
        )

        fb_account = self._get_fb_account('http://www.facebook.com/old_page', "1234")
        credentials = self.get_credentials()
        facebook_helper.update_facebook_account(fb_account, page_url, credentials['business_id'],
                                                credentials['access_token'])

        self.assertEqual(fb_account.page_url, page_url)
        self.assertEqual(fb_account.page_id, page_id)
        self.assertEqual(fb_account.status, constants.FacebookPageRequestType.PENDING)
        self.assertTrue(mock_page_id.called)
        self.assertTrue(mock_request.called)
        mock_stop.assert_called_once_with(fb_account.account)

    @patch('dash.facebook_helper.stop_facebook_media_sources')
    @patch('requests.get')
    @patch('requests.post')
    def test_update_clear_page(self, mock_request, mock_page_id, mock_stop):
        page_url = 'http://facebook.com/existing_page'
        page_id = '1234'
        fb_account = self._get_fb_account(page_url, page_id)
        credentials = self.get_credentials()
        facebook_helper.update_facebook_account(fb_account, None, credentials['business_id'],
                                                credentials['access_token'])

        self.assertEqual(fb_account.page_url, None)
        self.assertEqual(fb_account.page_id, None)
        self.assertEqual(fb_account.status, constants.FacebookPageRequestType.EMPTY)
        self.assertFalse(mock_request.called)
        self.assertFalse(mock_page_id.called)
        mock_stop.assert_called_once_with(fb_account.account)

    @patch('requests.post')
    def test_send_page_access_invalid_page(self, mock_post):
        mock_post.return_value = self._create_response(
            400,
            '{"error":{"message": "Code: (#100) Param page_id must be a valid page ID not your fake page id"}}',
        )

        page_id = 'invalid_page_id'
        credentials = self.get_credentials()
        status = facebook_helper.send_page_access_request(page_id, credentials['business_id'],
                                                          credentials['access_token'])

        mock_post.assert_called_once_with(
            FB_PAGES_URL.format(api_version=FB_API_VERSION, business_id='fake_business_id'),
            data=json.dumps(self._get_params(page_id)), headers=self._get_headers())
        self.assertEqual(status, constants.FacebookPageRequestType.INVALID)

    @patch('requests.post')
    def test_send_page_access_already_pending(self, mock):
        mock.return_value = self._create_response(
            400,
            '{"error":{"message": "Code: (#100) There is already pending client request for page pending_page_id"}}'
        )

        page_id = 'pending_page_id'
        credentials = self.get_credentials()
        status = facebook_helper.send_page_access_request(page_id, credentials['business_id'],
                                                          credentials['access_token'])

        mock.assert_called_once_with(FB_PAGES_URL.format(api_version=FB_API_VERSION, business_id='fake_business_id'),
                                     data=json.dumps(self._get_params(page_id)), headers=self._get_headers())
        self.assertEqual(status, constants.FacebookPageRequestType.PENDING)

    @patch('requests.post')
    def test_send_page_access_already_connected(self, mock):
        mock.return_value = self._create_response(
            400,
            '{"error":{"error_user_title": "Code: (#100) You Already Have Access To This Page"}}'
        )

        page_id = 'pending_page_id'
        credentials = self.get_credentials()
        status = facebook_helper.send_page_access_request(page_id, credentials['business_id'],
                                                          credentials['access_token'])

        mock.assert_called_once_with(FB_PAGES_URL.format(api_version=FB_API_VERSION, business_id='fake_business_id'),
                                     data=json.dumps(self._get_params(page_id)), headers=self._get_headers())
        self.assertEqual(status, constants.FacebookPageRequestType.CONNECTED)

    @patch('requests.post')
    def test_send_page_access_approval_sent_successfully(self, mock):
        mock.return_value = self._create_response(
            200,
            '{"dummy":{"dummy": "dummy"}}'
        )

        page_id = 'approve_me_page'
        credentials = self.get_credentials()
        status = facebook_helper.send_page_access_request(page_id, credentials['business_id'],
                                                          credentials['access_token'])

        mock.assert_called_once_with(FB_PAGES_URL.format(api_version=FB_API_VERSION, business_id='fake_business_id'),
                                     data=json.dumps(self._get_params(page_id)), headers=self._get_headers())
        self.assertEqual(status, constants.FacebookPageRequestType.PENDING)

    @patch('requests.post')
    def test_send_page_access_unknown_error(self, mock):
        mock.return_value = self._create_response(
            500,
            '{"dummy":{"dummy": "dummy"}}'
        )

        page_id = 'approve_me_page'
        credentials = self.get_credentials()
        status = facebook_helper.send_page_access_request(page_id, credentials['business_id'],
                                                          credentials['access_token'])

        mock.assert_called_once_with(FB_PAGES_URL.format(api_version=FB_API_VERSION, business_id='fake_business_id'),
                                     data=json.dumps(self._get_params(page_id)), headers=self._get_headers())
        self.assertEqual(status, constants.FacebookPageRequestType.ERROR)


class FacebookPagesTest(TestCase):
    @staticmethod
    def get_credentials():
        return {
            "app_id": "fake_app_id",
            "app_secret": "fake_app_secret",
            "access_token": "fake_access_token",
            "business_id": "fake_business_id",
            "system_user_id": "fake_system_user_id",
        }

    @staticmethod
    def _create_response(status_code, content):
        response = Response()
        response.status_code = status_code
        response._content = content
        return response

    @staticmethod
    def _get_token_json():
        return {'access_token': 'fake_access_token'}

    @patch('requests.get')
    def test_valid_page_id(self, mock_get):
        page_url = 'http://fb.com/page_name'
        mock_get.return_value = self._create_response(200, '{"id": "1234", "some_other_stuff": "i don\'t care about"}')

        credentials = self.get_credentials()
        page_id = facebook_helper.get_page_id(page_url, credentials['access_token'])
        mock_get.assert_called_once_with(FB_PAGE_ID_URL.format(api_version=FB_API_VERSION, page_id='page_name'),
                                         params=self._get_token_json())
        self.assertEqual(page_id, "1234")

    @patch('requests.get')
    def test_invalid_page_id(self, mock_get):
        page_url = 'http://fb.com/invalid_page'
        mock_get.return_value = self._create_response(400, '{"error": "Go away with this page"}')

        credentials = self.get_credentials()
        page_id = facebook_helper.get_page_id(page_url, credentials['access_token'])
        mock_get.assert_called_once_with(FB_PAGE_ID_URL.format(api_version=FB_API_VERSION, page_id='invalid_page'),
                                         params=self._get_token_json())
        self.assertEqual(page_id, None)

    def test_extract_page_id_from_url(self):
        expected_page_id = '1234'

        page_url = 'http://fb.com/dummy-dummy-1234'
        page_id = facebook_helper.extract_page_id_from_url(page_url)
        self.assertEqual(page_id, expected_page_id)

        page_url = 'http://fb.com/dummy-1234/'
        page_id = facebook_helper.extract_page_id_from_url(page_url)
        self.assertEqual(page_id, expected_page_id)

        page_url = '/dummy----1234/'
        page_id = facebook_helper.extract_page_id_from_url(page_url)
        self.assertEqual(page_id, expected_page_id)

        page_url = '/1234'
        page_id = facebook_helper.extract_page_id_from_url(page_url)
        self.assertEqual(page_id, expected_page_id)

        page_url = '1234/'
        page_id = facebook_helper.extract_page_id_from_url(page_url)
        self.assertEqual(page_id, expected_page_id)

        page_url = '1234'
        page_id = facebook_helper.extract_page_id_from_url(page_url)
        self.assertEqual(page_id, expected_page_id)

    @patch('requests.get')
    def test_get_all_pages(self, mock):
        response = {
            "data": [{"id": "first", "access_status": "connected"},
                     {"id": "second", "access_status": "pending"},
                     {"id": "third", "access_status": "unknown"}
                     ]}
        mock.return_value = self._create_response(200, json.dumps(response))

        credentials = self.get_credentials()
        pages_dict = facebook_helper.get_all_pages(credentials['business_id'], credentials['access_token'])

        expected = {'first': 'connected', 'second': 'pending', 'third': 'unknown'}
        self.assertEqual(pages_dict, expected)

    @patch('requests.get')
    def test_get_all_pages_error(self, mock):
        response = {
            "error": "invalid request"}
        mock.return_value = self._create_response(500, json.dumps(response))

        credentials = self.get_credentials()
        pages_dict = facebook_helper.get_all_pages(credentials['business_id'], credentials['access_token'])
        self.assertIsNone(pages_dict)


class FacebookAccountTest(TestCase):
    @staticmethod
    def get_credentials():
        return {
            "app_id": "fake_app_id",
            "app_secret": "fake_app_secret",
            "access_token": "fake_access_token",
            "business_id": "fake_business_id",
            "system_user_id": "fake_system_user_id",
        }

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
                'media_agency': 'fake_app_id',
                'partner': page_id,
                'access_token': 'fake_access_token'}

    @staticmethod
    def _get_user_params(role):
        return {'business': 'fake_business_id',
                'user': 'fake_system_user_id',
                'role': role,
                'access_token': 'fake_access_token'}

    @patch('requests.post')
    def test_create_ad_account(self, mock):
        mock.return_value = self._create_response(200, '{"id": "1000"}')

        name = 'dummy_name'
        page_id = '1234'
        credentials = self.get_credentials()
        ad_account_id = facebook_helper.create_ad_account(name, page_id, credentials['app_id'],
                                                          credentials['business_id'], credentials['access_token'])
        mock.assert_called_once_with(
            FB_AD_ACCOUNT_CREATE_URL.format(api_version=FB_API_VERSION, business_id='fake_business_id'),
            json.dumps(self._get_account_params(name, page_id)), headers=self._get_headers())
        self.assertEqual("1000", ad_account_id)

    @patch('requests.post')
    def test_create_ad_account_failed(self, mock):
        mock.return_value = self._create_response(500, '{"error": "invalid request"}')

        name = 'dummy_name'
        page_id = '1234'
        credentials = self.get_credentials()
        ad_account_id = facebook_helper.create_ad_account(name, page_id, credentials['app_id'],
                                                          credentials['business_id'], credentials['access_token'])
        mock.assert_called_once_with(FB_AD_ACCOUNT_CREATE_URL.format(api_version=FB_API_VERSION,
                                                                     business_id='fake_business_id'),
                                     json.dumps(self._get_account_params(name, page_id)), headers=self._get_headers())
        self.assertIsNone(ad_account_id)

    @patch('requests.post')
    def test_add_system_user_to_account(self, mock):
        mock.return_value = self._create_response(200, '')

        account_id = "1000"
        credentials = self.get_credentials()
        result = facebook_helper.add_system_user_permissions(account_id, 'ADMIN', credentials['business_id'],
                                                             credentials['system_user_id'], credentials['access_token'])
        mock.assert_called_once_with(FB_USER_PERMISSIONS_URL.format(api_version=FB_API_VERSION, object_id=account_id),
                                     json.dumps(self._get_user_params('ADMIN')), headers=self._get_headers())
        self.assertTrue(result)

    @patch('requests.post')
    def test_add_system_user_to_account_failed(self, mock):
        mock.return_value = self._create_response(500, 'some error we don\'t care about')

        account_id = "1000"
        credentials = self.get_credentials()
        result = facebook_helper.add_system_user_permissions(account_id, 'ADMIN', credentials['business_id'],
                                                             credentials['system_user_id'], credentials['access_token'])
        mock.assert_called_once_with(FB_USER_PERMISSIONS_URL.format(api_version=FB_API_VERSION, object_id=account_id),
                                     json.dumps(self._get_user_params('ADMIN')), headers=self._get_headers())
        self.assertFalse(result)

    @patch('requests.post')
    def test_add_system_user_to_page(self, mock):
        mock.return_value = self._create_response(200, '')

        page_id = "1234"
        credentials = self.get_credentials()
        result = facebook_helper.add_system_user_permissions(page_id, 'ADVERTISER', credentials['business_id'],
                                                             credentials['system_user_id'], credentials['access_token'])
        mock.assert_called_once_with(FB_USER_PERMISSIONS_URL.format(api_version=FB_API_VERSION, object_id=page_id),
                                     json.dumps(self._get_user_params('ADVERTISER')), headers=self._get_headers())
        self.assertTrue(result)

    @patch('requests.post')
    def test_add_system_user_to_page_failed(self, mock):
        mock.return_value = self._create_response(500, 'some error we don\'t care about')

        page_id = "1234"
        credentials = self.get_credentials()
        result = facebook_helper.add_system_user_permissions(page_id, 'ADVERTISER', credentials['business_id'],
                                                             credentials['system_user_id'], credentials['access_token'])
        mock.assert_called_once_with(FB_USER_PERMISSIONS_URL.format(api_version=FB_API_VERSION, object_id=page_id),
                                     json.dumps(self._get_user_params('ADVERTISER')), headers=self._get_headers())
        self.assertFalse(result)

    @patch('requests.get')
    def test_get_ad_account_status(self, get_mock):
        get_mock.return_value = self._create_response(200, '{"account_status":1,"id":"act_10153378392231753"}')
        credentials = self.get_credentials()
        account_status = facebook_helper.get_ad_account_status('act_10153378392231753', credentials['access_token'])
        self.assertEqual(account_status, models.constants.FacebookPageRequestType.CONNECTED)
        get_mock.assert_called_once_with('https://graph.facebook.com/v2.8/act_10153378392231753',
                                         params={'access_token': 'fake_access_token', 'fields': 'account_status'})


class FacebookStopMediaSourcesTest(TestCase):
    fixtures = ['test_views.yaml', 'test_facebook.yaml']

    @patch('utils.k1_helper.update_ad_groups')
    @patch('dash.models.AdGroupSourceSettings.save')
    def test_stop_source_on_account(self, save_mock, k1_update_mock):
        account = models.Account.objects.get(pk=100)
        facebook_helper.stop_facebook_media_sources(account)

        save_mock.assert_called_once_with(None)
        k1_update_mock.assert_called_once_with({100}, msg="facebook.stop_media_source")

    @patch('utils.k1_helper.update_ad_groups')
    @patch('dash.models.AdGroupSourceSettings.save')
    def test_stop_source_on_account_with_no_fb_sources(self, save_mock, k1_update_mock):
        account = models.Account.objects.get(pk=200)
        facebook_helper.stop_facebook_media_sources(account)

        self.assertFalse(save_mock.called)
        self.assertTrue(k1_update_mock.called)
