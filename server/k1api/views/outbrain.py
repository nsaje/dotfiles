from django.db import transaction
from django.db.models import F
from django.http import Http404

import dash.constants
import dash.models
from utils import db_router
from utils import outbrain_marketer_helper
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

        try:
            account = dash.models.Account.objects.get(campaign__adgroup__id=ad_group_id)
        except dash.models.Account.DoesNotExist:
            logger.exception("get_outbrain_marketer_id: ad group %s does not exist" % ad_group_id)
            raise Http404

        if account.outbrain_marketer_id is None:
            return self.response_error("Outbrain account not yet available.", 404)

        return self.response_ok(account.outbrain_marketer_id)


class OutbrainMarketerSyncView(K1APIView):
    def put(self, request):

        marketer_id = request.GET.get("marketer_id")
        marketer_name = request.GET.get("marketer_name")
        if not marketer_id:
            return self.response_error("Marketer id parameter is missing", status=400)

        used = False
        account_id = None
        marketer_version = None

        try:
            account_id, marketer_version = outbrain_marketer_helper.parse_marketer_name(marketer_name)
            used = True
        except ValueError:
            pass

        with transaction.atomic():
            try:
                ob_account = dash.models.OutbrainAccount.objects.select_for_update().get(marketer_id=marketer_id)
                if marketer_name and ob_account.marketer_name != marketer_name:
                    ob_account.marketer_name = marketer_name
                    ob_account.save()
                if not ob_account.used and used:
                    ob_account.used = used
                    ob_account.save()
                created = False
            except dash.models.OutbrainAccount.DoesNotExist:
                if not marketer_name:
                    return self.response_error("Marketer name parameter is missing", status=400)
                ob_account = dash.models.OutbrainAccount.objects.create(
                    marketer_id=marketer_id, marketer_name=marketer_name, used=used
                )
                created = True

            if account_id is not None:
                account = dash.models.Account.objects.select_for_update().get(id=account_id)
                if (
                    account.outbrain_marketer_version + 1 == marketer_version
                    and account.outbrain_marketer_id != marketer_id
                ):
                    k1_sync = marketer_id is None
                    account.update(
                        request,
                        k1_sync=k1_sync,
                        outbrain_marketer_id=marketer_id,
                        outbrain_marketer_version=marketer_version,
                    )

        return self.response_ok(
            {
                "created": created,
                "marketer_id": ob_account.marketer_id,
                "marketer_name": ob_account.marketer_name,
                "used": ob_account.used,
            }
        )
