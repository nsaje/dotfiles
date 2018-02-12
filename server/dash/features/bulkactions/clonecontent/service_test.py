from django.test import TestCase
from mock import patch
from utils.magic_mixer import magic_mixer

import core.entity
import core.source
from . import service


@patch.object(core.entity.ContentAd.objects, 'insert_redirects', autospec=True)
class Clone(TestCase):

    def test_clone(self, _):
        source_content_ads = magic_mixer.cycle(5).blend(core.entity.ContentAd)
        source_ad_group = magic_mixer.blend(core.entity.AdGroup)
        ad_group = magic_mixer.blend(core.entity.AdGroup)
        request = magic_mixer.blend_request_user()

        batch = service.clone(request, source_ad_group, source_content_ads, ad_group)

        self.assertCountEqual(
            [x.to_cloned_candidate_dict() for x in source_content_ads],
            [x.to_cloned_candidate_dict() for x in core.entity.ContentAd.objects.filter(batch=batch)]
        )

        self.assertEqual(batch.ad_group, ad_group)
