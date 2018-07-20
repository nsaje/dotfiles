from django.contrib import admin
from django.core.exceptions import ValidationError

from .models import SubmissionFilter
from .exceptions import SourcePolicyException, SubmissionFilterExistsException, MultipleFilterEntitiesException
from .constants import SubmissionFilterState


class SubmissionFilterAdmin(admin.ModelAdmin):
    raw_id_fields = ("content_ad", "ad_group", "campaign", "account", "agency")
    list_display = ("state", "source", "_agency", "_account", "_campaign", "_ad_group", "_content_ad")
    list_filter = ("state", "source")
    search_fields = (
        "source__name",
        "agency__id",
        "agency__name",
        "account__name",
        "account__id",
        "campaign__name",
        "campaign__id",
        "ad_group__name",
        "ad_group__id",
        "content_ad__id",
        "content_ad__title",
        "content_ad__brand_name",
    )
    readonly_fields = ("created_dt",)

    def save_model(self, request, obj, form, change):
        possible_keys = [obj.agency_id, obj.account_id, obj.campaign_id, obj.ad_group_id, obj.content_ad_id]
        if len([key for key in possible_keys if key is not None]) != 1:
            raise ValidationError("Multiple level entities not allowed.")
        try:
            _, level, level_id = obj.get_lookup_key()
            SubmissionFilter.objects.create(obj.source, obj.state, **{level + "_id": level_id})
        except SourcePolicyException:
            raise ValidationError(
                'State "{}" not allowed on this source'.format(SubmissionFilterState.get_text(obj.state))
            )
        except SubmissionFilterExistsException:
            raise ValidationError("Similar filter already exists.")
        except MultipleFilterEntitiesException:
            raise ValidationError("Multiple level entities not allowed.")

    def get_queryset(self, request):
        qs = super(SubmissionFilterAdmin, self).get_queryset(request)
        return qs.select_related("source", "content_ad", "ad_group", "campaign", "account", "agency")

    def _content_ad(self, obj):
        return obj.content_ad and "{}: {}".format(obj.content_ad_id, obj.content_ad.title) or ""

    def _ad_group(self, obj):
        return obj.ad_group and "{}: {}".format(obj.ad_group_id, obj.ad_group.name) or ""

    def _campaign(self, obj):
        return obj.campaign and "{}: {}".format(obj.campaign_id, obj.campaign.name) or ""

    def _account(self, obj):
        return obj.account and "{}: {}".format(obj.account_id, obj.account.name) or ""

    def _agency(self, obj):
        return obj.agency and "{}: {}".format(obj.agency_id, obj.agency.name) or ""
