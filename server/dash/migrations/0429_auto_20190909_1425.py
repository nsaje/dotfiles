# Generated by Django 2.1.11 on 2019-09-04 07:17

import django.db.models.deletion
from django.db import migrations
from django.db import models
from django.db import transaction

from utils import zlogging
from utils.queryset_helper import chunk_iterator

BATCH_SIZE = 1000
logger = zlogging.getLogger(__name__)


def populate_agency(apps, schema_editor):
    logger.info("Populating agency...")
    DirectDeal = apps.get_model("dash", "DirectDeal")

    deals_qs = DirectDeal.objects.all()

    chunk_number = 0
    for deals_chunk in chunk_iterator(deals_qs, chunk_size=BATCH_SIZE):
        chunk_number += 1
        logger.info("Processing chunk number %s...", chunk_number)

        with transaction.atomic():
            for deal in deals_chunk:
                for deal_connection in deal.directdealconnection_set.all():
                    agency = get_agency(deal_connection)
                    if agency is None:
                        # GLOBAL DEAL
                        continue
                    if deal.agency is None:
                        deal.agency = agency
                        deal.save()
                    elif deal.agency.id != agency.id:
                        # CASE WHEN THE SAME DEAL_ID HAS CONNECTIONS TO
                        # DIFFERENT AGENCY's
                        deal_copy = DirectDeal.objects.create(
                            deal_id=deal.deal_id,
                            description=deal.description,
                            name=deal.name,
                            source=deal.source,
                            agency=agency,
                            floor_price=deal.floor_price,
                            valid_from_date=deal.valid_from_date,
                            valid_to_date=deal.valid_to_date,
                            created_dt=deal.created_dt,
                            modified_dt=deal.modified_dt,
                            created_by=deal.created_by,
                        )
                        deal_copy.save()
                        deal_connection.deal = deal_copy
                        deal_connection.save()

        logger.info("Chunk number %s processed...", chunk_number)

    logger.info("Populating agency completed...")


def get_agency(deal_connection):
    if deal_connection.agency is not None:
        return deal_connection.agency
    elif deal_connection.account is not None:
        return deal_connection.account.agency
    elif deal_connection.campaign is not None:
        return deal_connection.campaign.account.agency
    elif deal_connection.adgroup is not None:
        return deal_connection.adgroup.campaign.account.agency
    else:
        return None


class Migration(migrations.Migration):
    atomic = False

    dependencies = [("dash", "0428_auto_20190909_1424")]

    operations = [
        migrations.AddField(
            model_name="directdeal",
            name="agency",
            field=models.ForeignKey(
                blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to="dash.Agency"
            ),
        ),
        migrations.RunPython(populate_agency, reverse_code=migrations.RunPython.noop),
    ]
