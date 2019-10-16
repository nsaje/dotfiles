
from django.conf import settings
from django.core.management import CommandError

import structlog
from dash import constants
from dash import facebook_helper
from dash import models
from utils.command_helpers import Z1Command

logger = structlog.get_logger(__name__)


class Command(Z1Command):
    def handle(self, *args, **options):
        # TODO matijav 07.07.2017 facebook disabled
        if settings.DISABLE_FACEBOOK:
            return

        credentials = facebook_helper.get_credentials()
        pending_accounts = models.FacebookAccount.objects.filter(status=constants.FacebookPageRequestType.PENDING)
        pages = facebook_helper.get_all_pages(credentials["business_id"], credentials["access_token"])
        if pages is None:
            raise CommandError("Error while accessing facebook page api.")

        for pending_account in pending_accounts:
            page_status = pages.get(pending_account.page_id)

            if page_status and page_status == "CONFIRMED":
                added = facebook_helper.add_system_user_permissions(
                    pending_account.page_id,
                    "ADVERTISER",
                    credentials["business_id"],
                    credentials["system_user_id"],
                    credentials["access_token"],
                )
                if not added:
                    raise CommandError(
                        "Error while adding system user to a connected object for account %s.",
                        pending_account.account.name,
                    )

                if not pending_account.ad_account_id:
                    ad_account_id = facebook_helper.create_ad_account(
                        pending_account.account.name,
                        pending_account.page_id,
                        credentials["app_id"],
                        credentials["business_id"],
                        credentials["access_token"],
                    )
                    if not ad_account_id:
                        raise CommandError(
                            "Error while creating facebook account for account %s.", pending_account.account.name
                        )
                    pending_account.ad_account_id = ad_account_id
                    pending_account.save()
                    logger.info(
                        "Facebook ad account for account %s created with id %s.",
                        pending_account.account.name,
                        ad_account_id,
                    )

                added = facebook_helper.add_system_user_permissions(
                    pending_account.ad_account_id,
                    "ADMIN",
                    credentials["business_id"],
                    credentials["system_user_id"],
                    credentials["access_token"],
                )
                if not added:
                    raise CommandError("Error while adding system user to a connected object.")

                pending_account.status = constants.FacebookPageRequestType.CONNECTED
                pending_account.save()
