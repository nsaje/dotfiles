import json

import boto.sqs
from boto.sqs.message import Message
from django.conf import settings

MAX_MESSAGES_PER_BATCH = 10


def _get_connection():
    return boto.sqs.connect_to_region(
        settings.SQS_REGION,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
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


def get_all_messages(queue_name):
    queue = _get_queue(_get_connection(), queue_name)
    rs = queue.get_messages(MAX_MESSAGES_PER_BATCH)
    messages = []
    while len(rs) > 0:
        messages.extend(rs)
        rs = queue.get_messages(MAX_MESSAGES_PER_BATCH)
    return messages


def delete_messages(queue_name, messages):
    connection = _get_connection()
    queue = _get_queue(connection, queue_name)
    for i in range(0, len(messages), MAX_MESSAGES_PER_BATCH):
        connection.delete_message_batch(
            queue, messages[i:i+MAX_MESSAGES_PER_BATCH])
