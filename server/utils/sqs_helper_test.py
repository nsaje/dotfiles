import json

from boto.sqs.message import Message
from django.test import TestCase
from mock import MagicMock
from mock import patch

from utils import sqs_helper


class WriteMessageTestCase(TestCase):
    @patch("utils.sqs_helper._get_connection")
    def test_write_message_json(self, mock_get_connection):
        queue_mock = MagicMock()
        conn_mock = MagicMock(**{"lookup.return_value": queue_mock})
        mock_get_connection.return_value = conn_mock

        queue_name = "test"
        message = {"param1": 1, "param2": "2"}

        sqs_helper.write_message_json(queue_name, message)
        self.assertTrue(conn_mock.lookup.called)
        self.assertTrue(queue_mock.write.called)
        self.assertEqual(1, queue_mock.write.call_count)
        self.assertEqual(json.dumps(message), queue_mock.write.call_args[0][0].get_body())


class DeleteMessagesTestCase(TestCase):
    @patch("utils.sqs_helper._get_connection")
    def test_delete_messages(self, mock_get_connection):
        queue_mock = MagicMock()
        conn_mock = MagicMock(**{"lookup.return_value": queue_mock})
        mock_get_connection.return_value = conn_mock

        queue_name = "test"
        message = Message(body='{"param": 1}')
        sqs_helper._delete_messages(queue_name, [message])

        conn_mock.delete_message_batch.assert_called_once_with(queue_mock, [message])


class ProcessJsonMessagesTestCase(TestCase):
    @patch("utils.sqs_helper._delete_messages")
    @patch("utils.sqs_helper._get_messages")
    def test_process_json_messages(self, mock_get_messages, mock_delete_messages):
        messages = [Message(body='{"property": "value"}')]
        mock_get_messages.return_value = messages

        with sqs_helper.process_json_messages("test", limit=100) as returned_messages:
            mock_get_messages.assert_called_once_with("test", limit=100)
            self.assertFalse(mock_delete_messages.called)
            self.assertCountEqual([{"property": "value"}], returned_messages)
        mock_get_messages.assert_called_once_with("test", limit=100)
        mock_delete_messages.assert_called_once_with("test", messages)
