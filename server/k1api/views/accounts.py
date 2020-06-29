from collections import defaultdict

from django.db import transaction
from django.db.models import Prefetch
from django.db.models import Q

import dash.constants
import dash.models
from utils import db_router
from utils import outbrain_marketer_helper
from utils import zlogging

from .base import K1APIView

logger = zlogging.getLogger(__name__)


OUTBRAIN_SOURCE_ID = 3


class AccountsView(K1APIView):
    @db_router.use_read_replica()
    def get(self, request):
        account_ids = request.GET.get("account_ids")
        accounts = (
            dash.models.Account.objects.all()
            .exclude_archived()
            .prefetch_related(
                Prefetch("conversionpixel_set", queryset=dash.models.ConversionPixel.objects.all().order_by("pk")),
                Prefetch(
                    "conversionpixel_set__sourcetypepixel_set",
                    queryset=(dash.models.SourceTypePixel.objects.all().order_by("pk").select_related("source_type")),
                ),
            )
        )
        if account_ids:
            accounts = accounts.filter(id__in=account_ids.split(","))

        accounts_audiences = self._get_audiences_for_accounts(accounts)
        account_dicts = []
        for account in accounts:
            pixels = []
            for pixel in account.conversionpixel_set.all():
                if pixel.archived:
                    continue

                source_pixels = []
                for source_pixel in pixel.sourcetypepixel_set.all():
                    source_pixel_dict = {
                        "url": source_pixel.url,
                        "source_pixel_id": source_pixel.source_pixel_id,
                        "source_type": source_pixel.source_type.type,
                    }
                    source_pixels.append(source_pixel_dict)

                pixel_dict = {
                    "id": pixel.id,
                    "name": pixel.name,
                    "slug": pixel.slug,
                    "audience_enabled": pixel.audience_enabled,
                    "additional_pixel": pixel.additional_pixel,
                    "source_pixels": source_pixels,
                }
                pixels.append(pixel_dict)

            account_dict = {
                "id": account.id,
                "agency_id": account.agency_id,
                "name": account.name,
                "pixels": pixels,
                "custom_audiences": accounts_audiences[account.id],
                "outbrain_marketer_id": account.outbrain_marketer_id,
                "outbrain_amplify_review_only": self._is_amplify_review_only(account),
                "default_cs_representative": (
                    account.settings.default_cs_representative
                    and account.settings.default_cs_representative.email
                    or None
                ),
            }
            account_dicts.append(account_dict)

        return self.response_ok(account_dicts)

    def _get_audiences_for_accounts(self, accounts):
        accounts_audiences = defaultdict(list)
        audiences = (
            dash.models.Audience.objects.all()
            .filter(pixel__account__in=accounts, archived=False)
            .select_related("pixel")
            .prefetch_related(
                Prefetch("audiencerule_set", queryset=dash.models.AudienceRule.objects.all().order_by("pk"))
            )
            .order_by("pk")
        )
        for audience in audiences:
            rules = []
            for rule in audience.audiencerule_set.all():
                rule_dict = {"id": rule.id, "type": rule.type, "values": rule.value}
                rules.append(rule_dict)

            audience_dict = {
                "id": audience.id,
                "name": audience.name,
                "pixel_id": audience.pixel.id,
                "ttl": audience.ttl,
                "prefill_days": audience.prefill_days,
                "rules": rules,
            }
            accounts_audiences[audience.pixel.account_id].append(audience_dict)
        return accounts_audiences

    def _is_amplify_review_only(self, account):
        return (
            dash.models.AdGroupSource.objects.filter(
                ad_group__campaign__account_id=account.id,
                ad_group__settings__archived=False,
                ad_review_only=True,
                source_id=OUTBRAIN_SOURCE_ID,
            ).exists()
            and not dash.models.AdGroupSource.objects.filter(
                ad_group__campaign__account_id=account.id,
                ad_group__settings__archived=False,
                source_id=OUTBRAIN_SOURCE_ID,
            )
            .filter(Q(ad_review_only=False) | Q(ad_review_only=None))
            .exists()
        )


class AccountMarketerView(K1APIView):
    def put(self, request, account_id):
        # validation of input parameters
        missing_required_fields = {"current_outbrain_marketer_id", "outbrain_marketer_id"} - request.data.keys()
        if missing_required_fields:
            return self.response_error("Missing attributes: %s" % ", ".join(missing_required_fields))

        current_marketer_id = request.data["current_outbrain_marketer_id"]
        desired_marketer_id = request.data["outbrain_marketer_id"]

        marketer_version = None

        if desired_marketer_id is not None:
            if "outbrain_marketer_name" not in request.data:
                return self.response_error("Missing required outbrain_marketer_name attribute")

            try:
                name_account_id, marketer_version = outbrain_marketer_helper.parse_marketer_name(
                    request.data["outbrain_marketer_name"]
                )
            except ValueError:
                return self.response_error("Invalid format of outbrain_marketer_name")

            if name_account_id != int(account_id):
                return self.response_error("Account ID mismatch")

        with transaction.atomic():
            try:
                account = dash.models.Account.objects.select_for_update().get(id=account_id)
            except dash.models.Account.DoesNotExist:
                return self.response_error("Account does not exist", status=404)

            if account.outbrain_marketer_id != current_marketer_id:
                return self.response_error("Invalid current Outbrain marketer id")

            if marketer_version is not None and account.outbrain_marketer_version + 1 != marketer_version:
                return self.response_error("Invalid Outbrain marketer version")

            # updating and creating entites
            if marketer_version is not None:
                dash.models.OutbrainAccount.objects.create(
                    marketer_id=desired_marketer_id, marketer_name=request.data["outbrain_marketer_name"], used=True
                )

            update_kwargs = {"outbrain_marketer_id": desired_marketer_id}
            if marketer_version is not None:
                update_kwargs.update({"outbrain_marketer_version": marketer_version})

            k1_sync = desired_marketer_id is None
            account.update(None, k1_sync=k1_sync, **update_kwargs)

        return self.response_ok(
            {
                "id": account.id,
                "outbrain_marketer_id": account.outbrain_marketer_id,
                "outbrain_marketer_version": account.outbrain_marketer_version,
            }
        )


class AccountMarketerParametersView(K1APIView):
    def get(self, request, account_id):
        try:
            account = dash.models.Account.objects.get(id=account_id)
        except dash.models.Account.DoesNotExist:
            return self.response_error("Account does not exist")

        marketer_type, content_classification = outbrain_marketer_helper.calculate_marketer_parameters(account_id)

        data = {
            "id": account.id,
            "created_dt": account.created_dt.isoformat(),
            "outbrain_marketer_id": account.outbrain_marketer_id,
            "outbrain_marketer_version": account.outbrain_marketer_version,
            "outbrain_marketer_type": marketer_type,
            "content_classification": content_classification,
            "emails": outbrain_marketer_helper.get_marketer_user_emails(),
        }
        return self.response_ok(data)


class AccountsBulkMarketerParametersView(K1APIView):
    @db_router.use_read_replica()
    def get(self, request):
        account_ids = request.GET.get("account_ids")

        account_data = dash.models.Account.objects.exclude_archived().filter(
            campaign__adgroup__adgroupsource__source_id=OUTBRAIN_SOURCE_ID
        )
        if account_ids:
            account_data = account_data.filter(id__in=account_ids.split(","))

        account_data = (
            account_data.distinct()
            .order_by("id")
            .values("id", "created_dt", "outbrain_marketer_id", "outbrain_marketer_version")
        )

        data = {"accounts": list(account_data), "emails": outbrain_marketer_helper.get_marketer_user_emails()}

        entries = (
            dash.models.EntityTag.objects.get(name=outbrain_marketer_helper.MARKETER_TYPE_PREFIX)
            .get_descendants()
            .filter(account__id__in=[e["id"] for e in data["accounts"]])
            .values("name", "account__id")
        )

        account_tag_map = defaultdict(list)
        for entry in entries:
            account_tag_map[entry["account__id"]].append(entry["name"])

        for entry in data["accounts"]:
            entity_tag_names = account_tag_map.get(entry["id"])
            marketer_type, content_classification = outbrain_marketer_helper.determine_best_match(entity_tag_names)
            entry.update(
                {
                    "created_dt": entry["created_dt"].isoformat(),
                    "outbrain_marketer_type": marketer_type,
                    "content_classification": content_classification,
                }
            )

        return self.response_ok(data)
