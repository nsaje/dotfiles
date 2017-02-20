import io
import re
import httplib2

import googleapiclient.discovery
from django.conf import settings
from googleapiclient.errors import HttpError
from oauth2client.service_account import ServiceAccountCredentials

from dash import constants

GA_SCOPE = ['https://www.googleapis.com/auth/analytics.readonly']
MANAGEMENT_API_NAME = 'analytics'
MANAGEMENT_API_VERSION = 'v3'
READ_AND_ANALYZE = 'READ_AND_ANALYZE'

_management_service = None


def is_readable(ga_property_id):
    if settings.R1_DEMO_MODE:
        return True
    management_service = _get_service()
    account_id = _extract_ga_account_id(ga_property_id)
    try:
        property_obj = management_service.management().webproperties().get(accountId=account_id, webPropertyId=ga_property_id).execute()
        if READ_AND_ANALYZE not in property_obj['permissions']['effective']:
            return False
        return True
    except HttpError as e:
        if 'insufficientPermissions' in e.content:
            return False
        raise


def _extract_ga_account_id(ga_property_id):
    result = re.search(constants.GA_PROPERTY_ID_REGEX, ga_property_id)
    return result.group(1)


def _get_service():
    global _management_service
    if _management_service:
        return _management_service

    key_buffer = io.BytesIO(settings.GA_PRIVATE_KEY)
    credentials = ServiceAccountCredentials(settings.GA_CLIENT_EMAIL, key_buffer, scope=GA_SCOPE)
    http = credentials.authorize(httplib2.Http())
    # Build the GA service object.
    _management_service = googleapiclient.discovery.build(MANAGEMENT_API_NAME, MANAGEMENT_API_VERSION, http=http,
                                                          discoveryServiceUrl=googleapiclient.discovery.DISCOVERY_URI,
                                                          cache_discovery=False)
    return _management_service
