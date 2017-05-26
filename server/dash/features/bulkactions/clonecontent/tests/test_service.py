from django.test import TestCase
from mock import patch
from utils.magic_mixer import magic_mixer

from dash.features.bulkactions import clonecontent
import core.entity
import core.source


@patch.object(core.entity.ContentAd.objects, 'insert_redirects')
class Clone(TestCase):

    def test_clone(self, _):
        source_content_ads = magic_mixer.cycle(5).blend(core.entity.ContentAd)
        source_ad_group = magic_mixer.blend(core.entity.AdGroup)
        ad_group = magic_mixer.blend(core.entity.AdGroup)
        user = magic_mixer.blend_user()

        batch = clonecontent.service.clone(user, source_ad_group, source_content_ads, ad_group)

        self.assertItemsEqual(
            [x.to_cloned_candidate_dict() for x in source_content_ads],
            [x.to_cloned_candidate_dict() for x in core.entity.ContentAd.objects.filter(batch=batch)]
        )

        self.assertEqual(batch.ad_group, ad_group)
