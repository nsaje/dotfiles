import json
import contextlib

import boto.sqs
from boto.sqs.message import Message
from django.conf import settings

MAX_MESSAGES_PER_BATCH = 10


def _get_connection():
    return boto.sqs.connect_to_region(
        settings.SQS_REGION,
    )


def _get_queue(connection, queue_name):
    queue = connection.lookup(queue_name)
    if queue is not None:
        return queue

    return connection.create_queue(queue_name, settings.SQS_VISIBILITY_TIMEOUT)


def write_message_json(queue_name, body):
    queue = _get_queue(_get_connection(), queue_name)
    message = Message()
    message.set_body(json.dumps(body))
    queue.write(message)


@contextlib.contextmanager
def process_messages_json(queue_name, num=50):
    messages = get_all_messages(queue_name, num)
    yield _get_json_content(messages)
    delete_messages(queue_name, messages)


def _get_json_content(messages):
    return [json.loads(message.get_body()) for message in messages]


def get_all_messages(queue_name, num):
    queue = _get_queue(_get_connection(), queue_name)
    messages = []
    while len(messages) < num:
        remaining = num - len(messages)
        num_to_fetch = min(MAX_MESSAGES_PER_BATCH, remaining)
        rs = queue.get_messages(num_to_fetch)
        messages.extend(rs)
        if len(rs) < num_to_fetch:
            break
    return messages


def delete_messages(queue_name, messages):
    connection = _get_connection()
    queue = _get_queue(connection, queue_name)
    for i in range(0, len(messages), MAX_MESSAGES_PER_BATCH):
        connection.delete_message_batch(
            queue, messages[i:i + MAX_MESSAGES_PER_BATCH])
