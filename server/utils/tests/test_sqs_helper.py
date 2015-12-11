import json

from boto.sqs.message import Message
from django.test import TestCase
from mock import patch, MagicMock

from utils import sqs_helper


class SqsHelperTestCase(TestCase):

    @patch('utils.sqs_helper._get_connection')
    def test_write_message_json(self, mock_get_connection):
        queue_mock = MagicMock()
        conn_mock = MagicMock(**{'create_queue.return_value': queue_mock})
        mock_get_connection.return_value = conn_mock

        queue_name = 'test'
        message = {
            'param1': 1,
            'param2': '2'
        }

        sqs_helper.write_message_json(queue_name, message)
        self.assertTrue(conn_mock.create_queue.called)
        self.assertTrue(queue_mock.write.called)
        self.assertEqual(1, queue_mock.write.call_count)
        self.assertEqual(json.dumps(message), queue_mock.write.call_args[0][0].get_body())

    @patch('utils.sqs_helper._get_connection')
    def test_get_all_messages_json(self, mock_get_connection):
        queue_mock = MagicMock()
        conn_mock = MagicMock(**{'create_queue.return_value': queue_mock})
        mock_get_connection.return_value = conn_mock

        queue_name = 'test'
        queue_mock.get_messages.side_effect = [
            [Message(body='{"param": 1}')],
            [Message(body='{"param": 2}')],
            [Message(body='{"param": 3}')],
            [Message(body='{"param": 4}')],
            [Message(body='{"param": 5}')],
            []
        ]

        messages = sqs_helper.get_all_messages_json(queue_name)
        self.assertEqual(6, queue_mock.get_messages.call_count)
        self.assertEqual([
            {'param': 1},
            {'param': 2},
            {'param': 3},
            {'param': 4},
            {'param': 5},
        ], messages)
