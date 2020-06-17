from django.db import transaction
from django.db.models import F
from django.http import Http404

import dash.constants
import dash.models
from utils import db_router
from utils import email_helper
from utils import zlogging

from .base import K1APIView

logger = zlogging.getLogger(__name__)


class OutbrainPublishersBlacklistView(K1APIView):
    @db_router.use_read_replica()
    def get(self, request):
        marketer_id = request.GET.get("marketer_id")
        account = {}
        blacklisted_publishers = []
        for acc in dash.models.Account.objects.filter(outbrain_marketer_id=marketer_id):
            # NOTE(sigi): sadly, we have some accounts with the same marketer id
            if acc.is_archived():
                continue
            account = {"id": acc.id, "name": acc.name, "outbrain_marketer_id": acc.outbrain_marketer_id}
            current_settings = acc.get_current_settings()
            blacklisted_publishers = (
                dash.models.PublisherGroupEntry.objects.filter(
                    publisher_group_id__in=(current_settings.blacklist_publisher_groups + [acc.default_blacklist_id])
                )
                .filter(source__bidder_slug="outbrain")
                .annotate(name=F("publisher"))
                .values("name")
            )
        return self.response_ok({"blacklist": list(blacklisted_publishers), "account": account})


class OutbrainMarketerIdView(K1APIView):
    def get(self, request):

        ad_group_id = request.GET.get("ad_group_id")

        with transaction.atomic():
            try:
                account = dash.models.Account.objects.select_for_update().get(campaign__adgroup__id=ad_group_id)
            except dash.models.Account.DoesNotExist:
                logger.exception("get_outbrain_marketer_id: ad group %s does not exist" % ad_group_id)
                raise Http404
            if account.outbrain_marketer_id:
                return self.response_ok(account.outbrain_marketer_id)

            try:
                unused_accounts = list(
                    dash.models.OutbrainAccount.objects.select_for_update().filter(used=False).order_by("created_dt")
                )

                if len(unused_accounts) == 10 or len(unused_accounts) == 3:
                    email_helper.send_outbrain_accounts_running_out_email(len(unused_accounts))

                outbrain_account = unused_accounts[0]

                outbrain_account.used = True
                outbrain_account.save()

                account.outbrain_marketer_id = outbrain_account.marketer_id
                account.save(request)

                logger.info(
                    "Assigned new Outbrain account",
                    ad_group_id=ad_group_id,
                    account_id=account.id,
                    marketer_id=outbrain_account.marketer_id,
                )

                try:
                    self.send_new_outbrain_account_used_email(account, outbrain_account)
                except Exception:
                    logger.exception(
                        "Could not send new Outbrain account assigned email",
                        ad_group_id=ad_group_id,
                        account_id=account.id,
                        marketer_id=outbrain_account.marketer_id,
                    )

            except IndexError:
                return self.response_error("No unused Outbrain accounts available.", 404)

        return self.response_ok(account.outbrain_marketer_id)

    @staticmethod
    def send_new_outbrain_account_used_email(account, outbrain_account):
        ob_info = (
            f"({outbrain_account.marketer_id})"
            if outbrain_account.marketer_name is None
            else f"{outbrain_account.marketer_name} ({outbrain_account.marketer_id})"
        )
        agency_info = "" if account.agency is None else f", Agency: {account.agency.name} ({account.agency.id})"
        body = (
            f"Assigned new Outbrain marketer {ob_info} for Zemanta Account: {account.name} ({account.id}){agency_info}"
        )
        email_helper.send_internal_email(
            recipient_list=["cs@zemanta.com"], subject="New Outbrain account / marketer assigned", body=body
        )


class OutbrainMarketerSyncView(K1APIView):
    def put(self, request):

        marketer_id = request.GET.get("marketer_id")
        marketer_name = request.GET.get("marketer_name")
        if not marketer_id:
            return self.response_error("Marketer id parameter is missing", status=400)
        try:
            ob_account = dash.models.OutbrainAccount.objects.get(marketer_id=marketer_id)
            if marketer_name and ob_account.marketer_name != marketer_name:
                ob_account.marketer_name = marketer_name
                ob_account.save()
            created = False
        except dash.models.OutbrainAccount.DoesNotExist:
            if not marketer_name:
                return self.response_error("Marketer name parameter is missing", status=400)
            ob_account = dash.models.OutbrainAccount.objects.create(
                marketer_id=marketer_id, marketer_name=marketer_name, used=False
            )
            created = True

        return self.response_ok(
            {
                "created": created,
                "marketer_id": ob_account.marketer_id,
                "marketer_name": ob_account.marketer_name,
                "used": ob_account.used,
            }
        )
