from django.test import TestCase
import dash.models
import dash.constants
import dash.retargeting_helper


class RetargetingHelperTest(TestCase):
    fixtures = ['test_models.yaml']

    def test_supports_retargeting_fail(self):
        settings = dash.models.AdGroupSourceSettings.objects.all().\
            filter(ad_group_source__ad_group_id=1).\
            group_current_settings().\
            select_related('ad_group_source')
        supports_retargeting, sources = dash.retargeting_helper.supports_retargeting(settings)
        self.assertFalse(supports_retargeting)
        self.assertEqual(1, len(sources))
        self.assertEqual(dash.constants.SourceType.ADBLADE, sources[0].source_type.type)

    def test_supports_retargeting(self):
        adblade = dash.models.Source.objects.filter(
            source_type__type=dash.constants.SourceType.ADBLADE
        ).first()
        adblade.maintenance = False
        adblade.deprecated = False
        adblade.save()

        settings = dash.models.AdGroupSourceSettings.objects.all().\
            filter(ad_group_source__ad_group_id=1).\
            group_current_settings().\
            select_related('ad_group_source')
        supports_retargeting, sources = dash.retargeting_helper.supports_retargeting(settings)
        self.assertTrue(supports_retargeting)
        self.assertEqual(0, len(sources))
