from django.test import TestCase

import influx_helper


class CleanPathTestCase(TestCase):

    def test_numeric_id(self):
        self.assertEqual('/adgroup/_ID_/sources/', influx_helper.clean_path('/adgroup/13/sources/'))

    def test_numeric_id_end(self):
        self.assertEqual('/adgroup/_ID_', influx_helper.clean_path('/adgroup/13'))

    def test_uuid(self):
        self.assertEqual('/videoassets/_UUID_/', influx_helper.clean_path('/videoassets/dd82ec82-f72b-4280-a273-8557e3034f16/'))

    def test_uuid_end(self):
        self.assertEqual('/videoassets/_UUID_', influx_helper.clean_path('/videoassets/dd82ec82-f72b-4280-a273-8557e3034f16'))

    def test_file(self):
        self.assertEqual('_FILE_', influx_helper.clean_path('/robots.txt'))
        self.assertEqual('_FILE_', influx_helper.clean_path('/Open Sans-Bold_2.ttf'))

    def test_token(self):
        self.assertEqual('/set_password/_TOKEN_/', influx_helper.clean_path('/set_password/MTM2MA-5ry-324dc45159f323fab67f/'))

    def test_token_end(self):
        self.assertEqual('/set_password/_TOKEN_', influx_helper.clean_path('/set_password/MTM2MA-5ry-324dc45159f323fab67f'))
