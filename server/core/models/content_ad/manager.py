from django.conf import settings
from django.db import models
from django.db import transaction

import core.models
import utils.redirector_helper
from dash import constants

from . import exceptions
from . import model


class ContentAdManager(models.Manager):
    @transaction.atomic
    def create(self, batch, sources, r1_resolve=True, **kwargs):
        content_ad = self._create(batch, sources, **kwargs)
        self.insert_redirects([content_ad], clickthrough_resolve=r1_resolve)
        return content_ad

    def _create(self, batch, sources, **kwargs):
        self._validate_archived(batch)

        content_ad = model.ContentAd(
            ad_group=batch.ad_group,
            batch=batch,
            amplify_review=batch.ad_group.amplify_review and settings.AMPLIFY_REVIEW,
            type={
                constants.CampaignType.VIDEO: constants.AdType.VIDEO,
                constants.CampaignType.DISPLAY: constants.AdType.IMAGE,
            }.get(batch.ad_group.campaign.type, constants.AdType.CONTENT),
        )

        for field in kwargs:
            if not hasattr(content_ad, field):
                continue
            setattr(content_ad, field, kwargs[field])

        content_ad.save()

        core.models.ContentAdSource.objects.bulk_create(content_ad, sources)

        return content_ad

    def _validate_archived(self, batch):
        if batch.ad_group.is_archived():
            raise exceptions.AdGroupIsArchived("Can not create a content ad on an archived ad group.")

    @transaction.atomic
    def bulk_create_from_candidates(self, candidate_dicts, batch, r1_resolve=True):
        ad_group_sources = core.models.AdGroupSource.objects.filter(
            ad_group=batch.ad_group
        ).filter_can_manage_content_ads()
        sources = core.models.Source.objects.filter(id__in=ad_group_sources.values_list("source_id", flat=True))

        content_ads = []
        for candidate in candidate_dicts:
            content_ads.append(self._create(batch, sources, **candidate))

        self.insert_redirects(content_ads, clickthrough_resolve=r1_resolve)

        return content_ads

    def bulk_clone(self, request, source_content_ads, ad_group, batch, overridden_state=None):
        candidates = [x.to_cloned_candidate_dict() for x in source_content_ads]
        if overridden_state is not None:
            for x in candidates:
                x["state"] = overridden_state

        # no need to resolve url in r1, because it was done before it was uploaded
        content_ads = self.bulk_create_from_candidates(candidates, batch, r1_resolve=False)
        ad_group.write_history_content_ads_cloned(
            request, content_ads, batch, source_content_ads[0].ad_group, overridden_state
        )

        return content_ads

    @transaction.atomic
    def insert_redirects(self, content_ads, clickthrough_resolve):
        redirector_batch = utils.redirector_helper.insert_redirects(
            content_ads, clickthrough_resolve=clickthrough_resolve
        )
        for content_ad in content_ads:
            content_ad.url = redirector_batch[str(content_ad.id)]["redirect"]["url"]
            content_ad.redirect_id = redirector_batch[str(content_ad.id)]["redirectid"]
            content_ad.save()
