import logging
from collections import defaultdict

from django.db.models import Prefetch
from django.db.models import Q

import dash.constants
import dash.models
from utils import db_for_reads

from .base import K1APIView

logger = logging.getLogger(__name__)


OUTBRAIN_SOURCE_ID = 3


class AccountsView(K1APIView):

    @db_for_reads.use_read_replica()
    def get(self, request):
        account_ids = request.GET.get('account_ids')
        accounts = (
            dash.models.Account.objects.all()
            .exclude_archived()
            .prefetch_related(
                Prefetch(
                    'conversionpixel_set',
                    queryset=dash.models.ConversionPixel.objects.all().order_by('pk'),
                ),
                Prefetch(
                    'conversionpixel_set__sourcetypepixel_set',
                    queryset=(
                        dash.models.SourceTypePixel.objects.all()
                        .order_by('pk')
                        .select_related('source_type')
                    ),
                )
            )
        )
        if account_ids:
            accounts = accounts.filter(id__in=account_ids.split(','))

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
                        'url': source_pixel.url,
                        'source_pixel_id': source_pixel.source_pixel_id,
                        'source_type': source_pixel.source_type.type,
                    }
                    source_pixels.append(source_pixel_dict)

                pixel_dict = {
                    'id': pixel.id,
                    'name': pixel.name,
                    'slug': pixel.slug,
                    'audience_enabled': pixel.audience_enabled,
                    'additional_pixel': pixel.additional_pixel,
                    'source_pixels': source_pixels,
                }
                pixels.append(pixel_dict)

            account_dict = {
                'id': account.id,
                'name': account.name,
                'pixels': pixels,
                'custom_audiences': accounts_audiences[account.id],
                'outbrain_marketer_id': account.outbrain_marketer_id,
                'outbrain_amplify_review_only': self._is_amplify_review_only(account),
            }
            account_dicts.append(account_dict)

        return self.response_ok(account_dicts)

    def _get_audiences_for_accounts(self, accounts):
        accounts_audiences = defaultdict(list)
        audiences = (
            dash.models.Audience.objects.all()
            .filter(pixel__account__in=accounts, archived=False)
            .select_related('pixel')
            .prefetch_related(Prefetch(
                'audiencerule_set',
                queryset=dash.models.AudienceRule.objects.all().order_by('pk'),
            ))
            .order_by('pk')
        )
        for audience in audiences:
            rules = []
            for rule in audience.audiencerule_set.all():
                rule_dict = {
                    'id': rule.id,
                    'type': rule.type,
                    'values': rule.value,
                }
                rules.append(rule_dict)

            audience_dict = {
                'id': audience.id,
                'name': audience.name,
                'pixel_id': audience.pixel.id,
                'ttl': audience.ttl,
                'prefill_days': audience.prefill_days,
                'rules': rules,
            }
            accounts_audiences[audience.pixel.account_id].append(audience_dict)
        return accounts_audiences

    def _is_amplify_review_only(self, account):
        return dash.models.AdGroupSource.objects.filter(
            ad_group__campaign__account_id=account.id,
            ad_group__settings__archived=False,
            ad_review_only=True,
            source_id=OUTBRAIN_SOURCE_ID,
        ).exists() and not dash.models.AdGroupSource.objects.filter(
            ad_group__campaign__account_id=account.id,
            ad_group__settings__archived=False,
            source_id=OUTBRAIN_SOURCE_ID,
        ).filter(Q(ad_review_only=False) | Q(ad_review_only=None)).exists()
