import json

import boto3

client = None


def get_client():
    global client
    if client is None:
        client = boto3.client('lambda')
    return client


def invoke_lambda(function, payload, async=False, **kwargs):
    response = get_client().invoke(
        FunctionName=function,
        Payload=json.dumps(payload),
        InvocationType=async and 'Event' or 'RequestResponse',
        **kwargs
    )
    return None if async else json.loads(response['Payload'].read())
