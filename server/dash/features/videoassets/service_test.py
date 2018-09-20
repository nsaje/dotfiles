import mock

import django.test

from . import service


@mock.patch("dash.features.videoassets.service.requests")
class TestParseVast(django.test.TestCase):
    def test_parse_vast(self, mock_requests):
        with open("./dash/features/videoassets/test_files/vast.xml") as f:
            data = f.read()

        expected = [{"bitrate": 500, "mime": "video/x-flv", "filename": "", "height": 300, "width": 400}]

        mock_requests.get.return_value.status_code = 200
        mock_requests.get.return_value.content = data

        duration, formats = service.parse_vast_from_url("test-url")

        mock_requests.get.assert_called_once_with("test-url")
        self.assertEqual(duration, 30)
        self.assertEqual(formats, expected)

    def test_parse_vast_wrapper(self, mock_requests):
        with open("./dash/features/videoassets/test_files/vast.xml") as f:
            data = f.read()
        with open("./dash/features/videoassets/test_files/vast_wrapper.xml") as f:
            data_wrapper = f.read()

        expected = [{"bitrate": 500, "mime": "video/x-flv", "filename": "", "height": 300, "width": 400}]

        return_vast = mock.Mock()
        return_vast.status_code = 200
        return_vast.content = data
        return_vast_wrapper = mock.Mock()
        return_vast_wrapper.status_code = 200
        return_vast_wrapper.content = data_wrapper
        mock_requests.get.side_effect = [return_vast_wrapper, return_vast]

        duration, formats = service.parse_vast_from_url("test-url")

        mock_requests.get.assert_any_call("test-url")
        mock_requests.get.assert_any_call("http://demo.tremormedia.com/proddev/vast/vast_inline_linear.xml")
        self.assertEqual(duration, 30)
        self.assertEqual(formats, expected)

    def test_parse_vast_moat(self, mock_requests):
        with open("./dash/features/videoassets/test_files/vast_moat.xml") as f:
            data = f.read()

        expected = [{"bitrate": None, "mime": "application/javascript", "filename": "", "height": 720, "width": 1280}]

        mock_requests.get.return_value.status_code = 200
        mock_requests.get.return_value.content = data

        duration, formats = service.parse_vast_from_url("test-url")

        mock_requests.get.assert_called_once_with("test-url")
        self.assertEqual(duration, 30)
        self.assertEqual(formats, expected)
