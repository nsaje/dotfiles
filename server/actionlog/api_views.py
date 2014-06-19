from django.views.decorators.csrf import csrf_exempt


@csrf_exempt
def zwei_callback(request, action_id):
    raise NotImplementedError
