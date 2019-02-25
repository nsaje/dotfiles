from django.test import TestCase

import core.models
from utils.magic_mixer import magic_mixer

from . import exceptions


class ValidationTestCase(TestCase):
    def test_create_pixel_archived(self):
        request = magic_mixer.blend_request_user()
        account = magic_mixer.blend(core.models.Account, users=[request.user])
        pixel = magic_mixer.blend(core.models.ConversionPixel, account=account, archived=True)
        with self.assertRaises(exceptions.PixelIsArchived):
            core.features.audiences.Audience.objects.create(
                request, "test", pixel, 10, 20, [{"type": 2, "value": "test_rule"}]
            )

    def test_create_rule_already_exists(self):
        request = magic_mixer.blend_request_user()
        account = magic_mixer.blend(core.models.Account, users=[request.user])
        pixel = magic_mixer.blend(core.models.ConversionPixel, account=account)
        core.features.audiences.Audience.objects.create(
            request, "test", pixel, 10, 20, [{"type": 2, "value": "test_rule"}]
        )
        with self.assertRaises(exceptions.RuleTtlCombinationAlreadyExists):
            core.features.audiences.Audience.objects.create(
                request, "test2", pixel, 10, 20, [{"type": 2, "value": "test_rule"}]
            )
        core.features.audiences.Audience.objects.create(
            request, "test2", pixel, 20, 20, [{"type": 2, "value": "test_rule"}]
        )
        core.features.audiences.Audience.objects.create(
            request, "test2", pixel, 10, 20, [{"type": 3, "value": "test_rule"}]
        )

    def test_can_not_be_archived_targeting(self):
        request = magic_mixer.blend_request_user()
        account = magic_mixer.blend(core.models.Account, users=[request.user])
        campaign = magic_mixer.blend(core.models.Campaign, account=account)
        pixel = magic_mixer.blend(core.models.ConversionPixel, account=account)
        audience = core.features.audiences.Audience.objects.create(
            request, "test", pixel, 10, 20, [{"type": 2, "value": "test_rule"}]
        )
        ad_group = magic_mixer.blend(core.models.AdGroup, campaign=campaign)
        ad_group.settings.update(request, audience_targeting=[audience.id])
        with self.assertRaises(exceptions.CanNotArchive):
            audience.update(request, archived=True)

    def test_can_not_be_archived_exclusion_targeting(self):
        request = magic_mixer.blend_request_user()
        account = magic_mixer.blend(core.models.Account, users=[request.user])
        campaign = magic_mixer.blend(core.models.Campaign, account=account)
        pixel = magic_mixer.blend(core.models.ConversionPixel, account=account)
        audience = core.features.audiences.Audience.objects.create(
            request, "test", pixel, 10, 20, [{"type": 2, "value": "test_rule"}]
        )
        ad_group = magic_mixer.blend(core.models.AdGroup, campaign=campaign)
        ad_group.settings.update(request, exclusion_audience_targeting=[audience.id])
        with self.assertRaises(exceptions.CanNotArchive):
            audience.update(request, archived=True)
