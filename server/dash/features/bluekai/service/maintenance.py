import logging

import bluekaiapi
from dash.features.bluekai import models
import utils.slack

logger = logging.getLogger(__name__)


AUDIENCE_ID = 202305
CAMPAIGN_ID = 151750
STATUS_ACTIVE = 'active'


def refresh_bluekai_categories():
    taxonomy = bluekaiapi.get_taxonomy()
    existing_categories = _get_existing_categories()
    new_categories, updated_categories = _get_updated_categories(
        taxonomy, existing_categories)

    for category in new_categories:
        models.BlueKaiCategory.objects.create(**category)

    for category in updated_categories:
        existing_categories[category['category_id']].update(
            name=category['name'],
            description=category['description'],
            reach=category['reach'],
            price=category['price'],
            navigation_only=category['navigation_only'],
        )


def cross_check_audience_categories():
    audience = bluekaiapi.get_audience(AUDIENCE_ID)
    active_categories = models.BlueKaiCategory.objects.active()

    messages = []
    segments = audience['segments']
    if segments.keys() != ['AND']:
        messages.append('Operator AND expected on top level')
    elif len(segments['AND']) != 1:
        messages.append('Top level AND has more than one child')
    elif segments['AND'][0].keys() != ['AND']:
        messages.append('Operator AND expected on second level')
    elif len(segments['AND'][0]['AND']) != 1:
        messages.append('Second level AND has more than one child')
    elif segments['AND'][0]['AND'][0].keys() != ['OR']:
        messages.append('Operator OR expected on third level')
    else:
        audience_categories = set(
            item['cat'] for item in segments['AND'][0]['AND'][0]['OR'])
        for category in active_categories:
            if category.category_id not in audience_categories:
                messages.append(
                    'Category {} is active in the system but '
                    'isn\'t added to the audience'.format(category.category_id)
                )

    if messages:
        messages = ['BlueKai campaign is out of sync with Z1. '
                    'Check https://partner.bluekai.com/rails/campaigns/{}. '
                    'Details:'.format(CAMPAIGN_ID)] + messages

    return '\n'.join(messages)


def _get_existing_categories():
    return {
        existing_category.category_id: existing_category
        for existing_category in models.BlueKaiCategory.objects.all()
    }


def _get_updated_categories(taxonomy, existing_categories):
    new_categories, updated_categories = [], []
    for bluekai_category in taxonomy:
        if bluekai_category['status'] != STATUS_ACTIVE:
            logger.warning(
                'BlueKai category not active. id=%s status=%s',
                bluekai_category['id'], bluekai_category['status']
            )

        category = {
            'category_id': bluekai_category['id'],
            'parent_category_id': bluekai_category['parentCategory']['id'],
            'name': bluekai_category['name'],
            'description': bluekai_category['description'],
            'reach': bluekai_category['stats']['reach'],
            'price': bluekai_category['categoryPrice'],
            'navigation_only': bluekai_category['isForNavigationOnlyFlag'],
        }
        print bluekai_category['stats']['reach'], bluekai_category['categoryPrice']

        existing_category = existing_categories.get(bluekai_category['id'])
        if not existing_category:
            new_categories.append(category)
            continue

        category['id'] = existing_category.pk
        updated_categories.append(category)

    return new_categories, updated_categories
