from __future__ import print_function
import json
import logging
import httplib

import requests
from django.core.management import CommandError

from utils.command_helpers import ExceptionCommand
from dash import models, constants
from django.conf import settings

logger = logging.getLogger(__name__)

FB_API_VERSION = "v2.6"
FB_PAGES_URL = "https://graph.facebook.com/{}/{}/pages"
FB_PAGE_ID_URL = "https://graph.facebook.com/{}/{}?fields=id"
FB_AD_ACCOUNT_URL = "https://graph.facebook.com/{}/{}/adaccount"
FB_USER_PERMISSIONS_URL = "https://graph.facebook.com/{}/{}/userpermissions"

TZ_AMERICA_NEW_YORK = 7
CURRENCY_USD = 'USD'


class Command(ExceptionCommand):
    def handle(self, *args, **options):
        pending_accounts = models.FacebookAccount.objects.filter(status=constants.FacebookPageRequestType.PENDING)
        pages = _get_all_pages()

        for pending_account in pending_accounts:
            page_status = pages.get(pending_account.page_id)

            if page_status and page_status == 'CONFIRMED':
                _add_system_user_permissions(page_id, 'ADVERTISER')
                ad_account_id = _create_ad_account(pending_account.account.name, page_id)
                _add_system_user_permissions(ad_account_id, 'ADMIN')

                pending_account.ad_account_id = ad_account_id
                pending_account.status = constants.FacebookPageRequestType.CONNECTED
                pending_account.save()


def _get_all_pages():
    params = {'access_token': settings.FB_ACCESS_TOKEN}
    response = requests.get(FB_PAGES_URL.format(FB_API_VERSION, settings.FB_BUSINESS_ID), params=params)

    if response.status_code != httplib.OK:
        logger.error('Error while accessing facebook page api. Status code: %s, Error %s', response.status_code,
                     response.content)
        raise CommandError('Error while accessing facebook page api.')

    content = response.json()
    pages_dict = {}
    for page in content.get('data'):
        pages_dict[page['id']] = page['access_status']

    return pages_dict


def _create_ad_account(name, page_id):
    params = {'name': name,
              'currency': CURRENCY_USD,
              'timezone_id': TZ_AMERICA_NEW_YORK,
              'end_advertiser': page_id,
              'media_agency': settings.FB_APP_ID,
              'partner': page_id,
              # TODO matijav 16.06.2016 disabled until we setup Business Manager Owned Normal Credit Line
              # 'invoice': True,
              'access_token': settings.FB_ACCESS_TOKEN}
    headers = {'Content-Type': 'application/json', 'Accept': 'application/json'}
    response = requests.post(FB_AD_ACCOUNT_URL.format(FB_API_VERSION, settings.FB_BUSINESS_ID), json.dumps(params),
                             headers=headers)
    if response.status_code != httplib.OK:
        logger.error('Error while creating facebook ad account. Status code: %s, Error %s', response.status_code,
                     response.content)
        raise CommandError('Error while creating facebook account.')

    content = response.json()
    return content['id']


def _add_system_user_permissions(connected_object_id, role):
    params = {'business': settings.FB_BUSINESS_ID,
              'user': settings.FB_SYSTEM_USER_ID,
              'role': role,
              'access_token': settings.FB_ACCESS_TOKEN}
    headers = {'Content-Type': 'application/json', 'Accept': 'application/json'}
    response = requests.post(FB_USER_PERMISSIONS_URL.format(FB_API_VERSION, connected_object_id), json.dumps(params),
                             headers=headers)
    if response.status_code != httplib.OK:
        logger.error('Error while adding system user to a connected object. Status code: %s, Error %s',
                     response.status_code, response.content)
        raise CommandError('Error while adding system user to a connected object.')
