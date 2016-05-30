import json

import boto3

client = boto3.client('lambda')


def invoke_lambda(function, payload, async=False, **kwargs):
    response = client.invoke(
        FunctionName=function,
        Payload=json.dumps(payload),
        InvocationType=async and 'Event' or 'RequestResponse',
        **kwargs
    )
    return None if async else json.loads(response['Payload'].read())
