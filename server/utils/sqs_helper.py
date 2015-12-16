import json

import boto.sqs
from boto.sqs.message import Message
from django.conf import settings


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
    rs = queue.get_messages(10)
    messages = []
    while len(rs) > 0:
        messages.extend(rs)
        rs = queue.get_messages(10)
    return messages


def delete_messages(queue_name, messages):
    connection = _get_connection()
    queue = _get_queue(connection, queue_name)
    connection.delete_message_batch(queue, messages)
