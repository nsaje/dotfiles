import json

from boto.sqs.message import Message
from django.test import TestCase
from mock import patch, MagicMock

from utils import sqs_helper


class SqsHelperTestCase(TestCase):

    @patch('utils.sqs_helper._get_connection')
    def test_write_message_json(self, mock_get_connection):
        queue_mock = MagicMock()
        conn_mock = MagicMock(**{'lookup.return_value': queue_mock})
        mock_get_connection.return_value = conn_mock

        queue_name = 'test'
        message = {
            'param1': 1,
            'param2': '2'
        }

        sqs_helper.write_message_json(queue_name, message)
        self.assertTrue(conn_mock.lookup.called)
        self.assertTrue(queue_mock.write.called)
        self.assertEqual(1, queue_mock.write.call_count)
        self.assertEqual(json.dumps(message), queue_mock.write.call_args[0][0].get_body())

    @patch('utils.sqs_helper._get_connection')
    def test_get_all_messages(self, mock_get_connection):
        queue_mock = MagicMock()
        conn_mock = MagicMock(**{'lookup.return_value': queue_mock})
        mock_get_connection.return_value = conn_mock

        message1 = Message(body='{"param": 1}')
        message2 = Message(body='{"param": 2}')
        message3 = Message(body='{"param": 3}')
        message4 = Message(body='{"param": 4}')
        message5 = Message(body='{"param": 5}')

        queue_name = 'test'
        queue_mock.get_messages.side_effect = [
            [message1],
            [message2],
            [message3],
            [message4],
            [message5],
            []
        ]
        self.maxDiff = None

        messages = sqs_helper.get_all_messages(queue_name)
        self.assertEqual(6, queue_mock.get_messages.call_count)
        self.assertItemsEqual([
            message1,
            message2,
            message3,
            message4,
            message5,
        ], messages)

    @patch('utils.sqs_helper._get_connection')
    def test_delete_messages(self, mock_get_connection):
        queue_mock = MagicMock()
        conn_mock = MagicMock(**{'lookup.return_value': queue_mock})
        mock_get_connection.return_value = conn_mock

        queue_name = 'test'
        message = Message(body='{"param": 1}')
        sqs_helper.delete_messages(queue_name, [message])

        conn_mock.delete_message_batch.assert_called_once_with(queue_mock, [message])
