import io
import re
import httplib2

import googleapiclient.discovery
from django.conf import settings
from django.db import transaction
from oauth2client.service_account import ServiceAccountCredentials

from dash import constants

import models

GA_SCOPE = ['https://www.googleapis.com/auth/analytics.readonly']
MANAGEMENT_API_NAME = 'analytics'
MANAGEMENT_API_VERSION = 'v3'
READ_AND_ANALYZE = 'READ_AND_ANALYZE'

_management_services = {}


def is_readable(ga_property_id):
    if settings.R1_DEMO_MODE:
        return True
    account_id = extract_ga_account_id(ga_property_id)
    if models.GALinkedAccounts.objects.filter(customer_ga_account_id=account_id, has_read_and_analyze=True).exists():
        return True

    try:
        refresh_mappings()
        if models.GALinkedAccounts.objects.filter(customer_ga_account_id=account_id, has_read_and_analyze=True).exists():
            return True
    except Exception:
        # if it's not in our mapping table and the refresh fails, it won't hurt to report it as inaccessible
        pass
    return False


@transaction.atomic()
def refresh_mappings():
    mapping_objects = {}
    for zem_ga_account_email in settings.GA_CREDENTIALS:
        management_service = _get_service(zem_ga_account_email)
        linked_ga_accounts = management_service.management().accounts().list().execute()['items']
        for ga_account in linked_ga_accounts:
            existing_mapping = mapping_objects.get(ga_account['id'])
            if existing_mapping and existing_mapping.has_read_and_analyze:
                continue
            mapping_objects[ga_account['id']] = models.GALinkedAccounts(
                customer_ga_account_id=ga_account['id'],
                zem_ga_account_email=zem_ga_account_email,
                has_read_and_analyze=READ_AND_ANALYZE in ga_account['permissions']['effective']
            )
    models.GALinkedAccounts.objects.all().delete()
    models.GALinkedAccounts.objects.bulk_create(mapping_objects.values())


def extract_ga_account_id(ga_property_id):
    result = re.search(constants.GA_PROPERTY_ID_REGEX, ga_property_id)
    return result.group(1)


def _get_service(zem_ga_account_email):
    global _management_services
    management_service = _management_services.get(zem_ga_account_email)
    if management_service:
        return management_service

    assert zem_ga_account_email in settings.GA_CREDENTIALS

    key_buffer = io.BytesIO(settings.GA_CREDENTIALS[zem_ga_account_email])
    credentials = ServiceAccountCredentials.from_p12_keyfile_buffer(zem_ga_account_email, key_buffer, scopes=GA_SCOPE)
    http = credentials.authorize(httplib2.Http())
    # Build the GA service object.
    management_service = googleapiclient.discovery.build(MANAGEMENT_API_NAME, MANAGEMENT_API_VERSION, http=http,
                                                         discoveryServiceUrl=googleapiclient.discovery.DISCOVERY_URI,
                                                         cache_discovery=False)
    _management_services[zem_ga_account_email] = management_service
    return management_service
