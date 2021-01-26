import json

import boto3
from django.conf import settings

client = None


def get_client(**kwargs):
    global client
    if client is None:
        client = boto3.client("lambda", **kwargs)
    return client


def invoke_lambda(function, payload, do_async=False, **kwargs):
    response = get_client(region_name=settings.LAMBDA_REGION).invoke(
        FunctionName=function,
        Payload=json.dumps(payload),
        InvocationType=do_async and "Event" or "RequestResponse",
        **kwargs,
    )
    return None if do_async else json.loads(response["Payload"].read())
