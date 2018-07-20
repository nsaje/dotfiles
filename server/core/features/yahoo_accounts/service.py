from . import YahooAccount

import dateutil.parser
from django.db import transaction

import core.entity
import core.features.yahoo_accounts
import dash.constants
import utils.dates_helper

from . import constants
from . import models

DEFAULT_ADVERTISER_ID = "953699"


def get_default_account():
    return YahooAccount.objects.get(advertiser_id=DEFAULT_ADVERTISER_ID)


class CannotRunMigrationException(Exception):
    pass


@transaction.atomic
def finalize_migration(account_id, direct_migration=False, advertiser_id=None, currency=None):
    account = core.entity.Account.objects.get(pk=account_id)

    if direct_migration:
        migration = {
            "status": constants.MIGRATION_STATUS_SWITCHOVER,
            "advertiser_id": advertiser_id,
            "currency": currency,
            "switchover_date": str(utils.dates_helper.local_today()),
        }
    else:
        migration = utils.k1_helper.get_yahoo_migration(account_id)

    if migration is None:
        raise CannotRunMigrationException("Migration for this account does not exist")
    if migration["status"] != constants.MIGRATION_STATUS_SWITCHOVER:
        raise CannotRunMigrationException("Finalize migration can be run only for migrations in switchover")
    switchover_date = dateutil.parser.parse(migration["switchover_date"]).date()
    if switchover_date > utils.dates_helper.local_today():
        raise CannotRunMigrationException("Finalize migration can only be run after switchover date")
    if not migration["currency"]:
        raise CannotRunMigrationException("No currency set for migration")
    if not migration["advertiser_id"]:
        raise CannotRunMigrationException("No advertiser id set for migration")
    if account.yahoo_account.advertiser_id == migration["advertiser_id"]:
        raise CannotRunMigrationException("This account already has this advertiser id")

    update_yahoo_account(account, migration)

    if direct_migration:
        source_campaign_key_mapping = {}
    else:
        source_campaign_key_mapping = {
            item["z1_id"]: str(item["new"])
            for item in utils.k1_helper.get_yahoo_migration_campaign_mappings(account_id)
        }
    update_source_campaign_keys(account, source_campaign_key_mapping)

    if direct_migration:
        source_content_ad_id_mapping = {}
    else:
        source_content_ad_id_mapping = {
            item["z1_id"]: int(item["new"])
            for item in utils.k1_helper.get_yahoo_migration_content_ad_mappings(account_id)
        }
    update_source_content_ad_ids(account, source_content_ad_id_mapping)

    if not direct_migration:
        utils.k1_helper.update_yahoo_migration(account_id, status=constants.MIGRATION_STATUS_FINISHED)


def update_source_content_ad_ids(account, mapping):
    content_ad_sources = (
        core.entity.ContentAdSource.objects.all()
        .select_related("content_ad")
        .filter(content_ad__ad_group__campaign__account=account)
        .filter(source__source_type__type=dash.constants.SourceType.YAHOO)
    )
    for content_ad_source in content_ad_sources:
        models.YahooMigrationContentAdHistory.objects.create(
            content_ad=content_ad_source.content_ad, source_content_ad_id=content_ad_source.source_content_ad_id
        )
        content_ad_source.source_content_ad_id = mapping.get(content_ad_source.content_ad_id)
        content_ad_source.save()


def update_source_campaign_keys(account, mapping):
    ad_group_sources = (
        core.entity.AdGroupSource.objects.all()
        .select_related("ad_group")
        .filter(ad_group__campaign__account=account)
        .filter(source__source_type__type=dash.constants.SourceType.YAHOO)
    )
    for ad_group_source in ad_group_sources:
        models.YahooMigrationAdGroupHistory.objects.create(
            ad_group=ad_group_source.ad_group, source_campaign_key=ad_group_source.source_campaign_key
        )
        ad_group_source.source_campaign_key = mapping.get(ad_group_source.ad_group_id, {})
        ad_group_source.save()


def update_yahoo_account(account, data):
    yahoo_account, _ = core.features.yahoo_accounts.YahooAccount.objects.get_or_create(
        advertiser_id=data["advertiser_id"], defaults={"currency": data["currency"]}
    )
    account.yahoo_account = yahoo_account
    account.save(None)
