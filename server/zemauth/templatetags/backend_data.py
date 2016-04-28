import json

from django import template
from django.conf import settings

register = template.Library()


def is_demo_user(user):
    return user.email == settings.DEMO_USER_EMAIL or user.email in settings.DEMO_USERS


@register.inclusion_tag('backend_data.html', takes_context=True)
def js_data(context):
    request = context['request']
    return {
        'window_data': {
            'isDemo': json.dumps(is_demo_user(request.user))
        }
    }
