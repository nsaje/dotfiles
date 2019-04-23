from django.db import models

import core.common
import core.models.helpers
import dash.constants

from . import constants
from . import exceptions


class SubmissionFilterManager(core.common.BaseManager):
    @staticmethod
    def validate(source, state, entities, check_existing=True):
        if len(entities) != 1:
            raise exceptions.MultipleFilterEntitiesException("Multiple level entities not allowed.")
        if (source.content_ad_submission_policy, state) not in (
            (dash.constants.SourceSubmissionPolicy.AUTOMATIC, constants.SubmissionFilterState.BLOCK),
            (
                dash.constants.SourceSubmissionPolicy.AUTOMATIC_WITH_AMPLIFY_APPROVAL,
                constants.SubmissionFilterState.BLOCK,
            ),
            (dash.constants.SourceSubmissionPolicy.MANUAL, constants.SubmissionFilterState.ALLOW),
        ):
            raise exceptions.SourcePolicyException('State "{}" not allowed on this source'.format(state))
        if check_existing and SubmissionFilter.objects.filter(source=source, **entities).exists():
            raise exceptions.SubmissionFilterExistsException("Similar filter already exists.")

    def create(self, source, state, **entities):
        self.validate(source, state, entities)
        sf = SubmissionFilter(source=source, state=state, **entities)
        sf.save()
        return sf

    def bulk_create(self, source, state, lookup_level, lookup_ids):
        self.validate(source, state, {lookup_level + "_id__in": lookup_ids})
        values = [
            SubmissionFilter(source=source, state=state, **{lookup_level + "_id": lookup_id})
            for lookup_id in set(lookup_ids)
        ]
        return super(SubmissionFilterManager, self).bulk_create(values)


class SubmissionFilter(models.Model):
    id = models.AutoField(primary_key=True)
    source = models.ForeignKey("Source", related_name="submission_filters", on_delete=models.PROTECT)

    agency = models.ForeignKey(
        "Agency", null=True, blank=True, related_name="submission_filters", on_delete=models.PROTECT
    )
    account = models.ForeignKey(
        "Account", null=True, blank=True, related_name="submission_filters", on_delete=models.PROTECT
    )
    campaign = models.ForeignKey(
        "Campaign", null=True, blank=True, related_name="submission_filters", on_delete=models.PROTECT
    )
    ad_group = models.ForeignKey(
        "AdGroup", null=True, blank=True, related_name="submission_filters", on_delete=models.PROTECT
    )
    content_ad = models.ForeignKey(
        "ContentAd", null=True, blank=True, related_name="submission_filters", on_delete=models.PROTECT
    )

    state = models.IntegerField(
        default=constants.SubmissionFilterState.BLOCK, choices=constants.SubmissionFilterState.get_choices()
    )

    created_dt = models.DateTimeField(auto_now_add=True, verbose_name="Created at")
    modified_dt = models.DateTimeField(auto_now=True, verbose_name="Modified at")
    description = models.TextField(null=True, blank=True)

    def get_lookup_key(self):
        if self.content_ad_id:
            return (self.source_id, "content_ad", self.content_ad_id)
        if self.ad_group_id:
            return (self.source_id, "ad_group", self.ad_group_id)
        if self.campaign_id:
            return (self.source_id, "campaign", self.campaign_id)
        if self.account_id:
            return (self.source_id, "account", self.account_id)
        if self.agency_id:
            return (self.source_id, "agency", self.agency_id)

    def __str__(self):
        return "{} ads on source {} and {} level: {}".format(
            constants.SubmissionFilterState.get_text(self.state), *self.get_lookup_key()
        )

    class QuerySet(models.QuerySet):
        def filter_applied(self, source, content_ad=None, **levels):
            ad_group = levels.get("ad_group") or content_ad and content_ad.ad_group
            campaign, account, agency = core.models.helpers.generate_parents(**levels)
            rules = models.Q()
            if agency:
                rules |= models.Q(agency=agency)
            if account:
                rules |= models.Q(account=account)
            if campaign:
                rules |= models.Q(campaign=campaign)
            if ad_group:
                rules |= models.Q(ad_group=ad_group)
            if content_ad:
                rules |= models.Q(content_ad=content_ad)
            return self.filter(rules).filter(source=source)

    objects = SubmissionFilterManager.from_queryset(QuerySet)()
