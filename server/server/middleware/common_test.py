from unittest import mock

from django.test import RequestFactory
from django.test import TestCase

import utils.rest_common.authentication
from utils.magic_mixer import magic_mixer

from . import common


class CleanPathTestCase(TestCase):
    def test_numeric_id(self):
        self.assertEqual("/adgroup/_ID_/sources/", common.clean_path("/adgroup/13/sources/"))

    def test_numeric_id_end(self):
        self.assertEqual("/adgroup/_ID_", common.clean_path("/adgroup/13"))

    def test_uuid(self):
        self.assertEqual(
            "/videoassets/_UUID_/", common.clean_path("/videoassets/dd82ec82-f72b-4280-a273-8557e3034f16/")
        )

    def test_uuid_end(self):
        self.assertEqual("/videoassets/_UUID_", common.clean_path("/videoassets/dd82ec82-f72b-4280-a273-8557e3034f16"))

    def test_file(self):
        self.assertEqual("_FILE_", common.clean_path("/robots.txt"))
        self.assertEqual("_FILE_", common.clean_path("/Open Sans-Bold_2.ttf"))

    def test_token(self):
        self.assertEqual("/set_password/_TOKEN_/", common.clean_path("/set_password/MTM2MA-5ry-324dc45159f323fab67f/"))

    def test_token_end(self):
        self.assertEqual("/set_password/_TOKEN_", common.clean_path("/set_password/MTM2MA-5ry-324dc45159f323fab67f"))


class ExtractRequestParamsTestCase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    @mock.patch.object(common, "clean_path", return_value="sanitized")
    def test_low_cardinality(self, mock_clean_path):
        request = self.factory.get("/my/123/path?param1=a&param2=b")
        self.assertEqual(common.extract_request_params(request, high_cardinality=False)["path"], "sanitized")
        mock_clean_path.assert_called_once_with("/my/123/path")

    def test_high_cardinality(self):
        request = self.factory.get("/my/123/path?param1=a&param2=b")
        self.assertEqual(
            common.extract_request_params(request, high_cardinality=True)["path"], "/my/123/path?param1=a&param2=b"
        )

    def test_authenticator_session(self):
        request = self.factory.get("/my/path")
        self.assertEqual(common.extract_request_params(request)["authenticator"], "session")

    def test_authenticator_oauth2(self):
        request = self.factory.get("/my/path")
        request.successful_authenticator = utils.rest_common.authentication.OAuth2Authentication()
        self.assertEqual(common.extract_request_params(request)["authenticator"], "oauth2")

    def test_no_user(self):
        request = self.factory.get("/my/path")
        self.assertEqual(common.extract_request_params(request)["user"], "unknown")

    def test_user(self):
        request = self.factory.get("/my/path")
        request.user = magic_mixer.blend_user()
        self.assertEqual(common.extract_request_params(request)["user"], request.user.email)
