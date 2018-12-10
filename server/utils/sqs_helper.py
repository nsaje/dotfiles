import contextlib
import json

import boto.sqs
from boto.sqs.message import Message
from django.conf import settings

MAX_MESSAGES_PER_BATCH = 10


def _get_connection():
    return boto.sqs.connect_to_region(settings.SQS_REGION)


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
def process_json_messages(queue_name, limit=None):
    messages = _get_messages(queue_name, limit=limit)
    yield _get_json_content(messages)
    _delete_messages(queue_name, messages)


def _get_messages(queue_name, *, limit):
    queue = _get_queue(_get_connection(), queue_name)
    rs = queue.get_messages(min(limit, MAX_MESSAGES_PER_BATCH))
    messages = rs[:]
    while len(rs) > 0 and (not limit or len(messages) < limit):
        num_to_fetch = _calculate_num_to_fetch(messages, limit)
        rs = queue.get_messages(num_to_fetch)
        messages.extend(rs)
    return messages


def _calculate_num_to_fetch(existing_messages, limit):
    if limit is None:
        return MAX_MESSAGES_PER_BATCH
    missing_to_limit = limit - len(existing_messages)
    if missing_to_limit < MAX_MESSAGES_PER_BATCH:
        return max(0, missing_to_limit)
    return MAX_MESSAGES_PER_BATCH


def _get_json_content(messages):
    return [json.loads(message.get_body()) for message in messages]


def _delete_messages(queue_name, messages):
    connection = _get_connection()
    queue = _get_queue(connection, queue_name)
    for i in range(0, len(messages), MAX_MESSAGES_PER_BATCH):
        connection.delete_message_batch(queue, messages[i : i + MAX_MESSAGES_PER_BATCH])
