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


def write_message_json(queue_name, body):
    conn = _get_connection()
    queue = conn.create_queue(queue_name, settings.SQS_VISIBILITY_TIMEOUT)
    message = Message()
    message.set_body(json.dumps(body))
    queue.write(message)


def get_all_messages_json(queue_name):
    conn = _get_connection()
    queue = conn.create_queue(queue_name, settings.SQS_VISIBILITY_TIMEOUT)
    rs = queue.get_messages(10)
    messages = []
    while len(rs) > 0:
        messages.extend([json.loads(message.get_body()) for message in rs])
        rs = queue.get_messages(10)
    return messages
