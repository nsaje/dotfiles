from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render


@csrf_exempt
def accounts(request, action_id):
    logger.debug('Received zwei callback: %s', action_id)

    _validate_callback(request, action_id)
    action = _get_action(action_id)

    data = json.loads(request.body)
    try:
        _process_zwei_response(action, data, request)
        _update_last_successful_sync_dt(action, request)
    except Exception as e:
        _handle_zwei_callback_error(e, action)

    response_data = {'status': 'OK'}
    return JsonResponse(response_data)


def _validate_callback(request, action_id):
    '''
    if the request is not valid this raises an exception
    '''
    try:
        request_signer.verify_wsgi_request(request, settings.ZWEI_API_SIGN_KEY)
    except request_signer.SignatureError as e:
        logger.exception('Invalid zwei callback signature.')

        msg = 'Zwei callback failed for action: %s. Error: %s'
        logger.error(msg, action_id, repr(e.message))
