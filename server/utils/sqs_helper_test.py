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


@patch("utils.sqs_helper.MAX_MESSAGES_PER_BATCH", 2)
class GetMessagesTestCase(TestCase):
    def setUp(self):
        self.queue_name = "test"

        self.message1 = Message(body='{"param": 1}')
        self.message2 = Message(body='{"param": 2}')
        self.message3 = Message(body='{"param": 3}')
        self.message4 = Message(body='{"param": 4}')
        self.message5 = Message(body='{"param": 5}')
        self.messages = [self.message1, self.message2, self.message3, self.message4, self.message5]
        self._prepare_get_connection_mock()
        self._init_get_messages_mock(self.messages)

    def _prepare_get_connection_mock(self):
        patcher = patch("utils.sqs_helper._get_connection")
        mock_get_connection = patcher.start()
        self.queue_mock = MagicMock()
        conn_mock = MagicMock(**{"lookup.return_value": self.queue_mock})
        mock_get_connection.return_value = conn_mock
        self.addCleanup(patcher.stop)

    def _init_get_messages_mock(self, list_):
        def _get_messages_mock(num):
            nonlocal index
            ret = list_[index : index + num]
            index += num
            return ret

        index = 0
        self.queue_mock.get_messages.side_effect = _get_messages_mock

    def test_get_messages(self):
        messages_received = sqs_helper._get_messages(self.queue_name, limit=10)
        self.assertEqual(4, self.queue_mock.get_messages.call_count)
        self.assertCountEqual(
            [self.message1, self.message2, self.message3, self.message4, self.message5], messages_received
        )

    def test_get_messages_limit(self):
        messages_received = sqs_helper._get_messages(self.queue_name, limit=3)
        self.assertEqual(2, self.queue_mock.get_messages.call_count)
        self.assertCountEqual([self.message1, self.message2, self.message3], messages_received)
