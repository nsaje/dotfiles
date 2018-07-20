from django.test import TestCase
import dash.models
import dash.constants
import dash.retargeting_helper


class RetargetingHelperTest(TestCase):
    fixtures = ["test_models.yaml"]

    def test_supports_retargeting_fail(self):
        ad_group_sources = (
            dash.models.AdGroup.objects.get(pk=1).adgroupsource_set.all().select_related("source", "settings")
        )
        supports_retargeting, sources = dash.retargeting_helper.supports_retargeting(ad_group_sources)
        self.assertFalse(supports_retargeting)
        self.assertEqual(1, len(sources))
        self.assertEqual(dash.constants.SourceType.ADBLADE, sources[0].source_type.type)

    def test_supports_retargeting(self):
        adblade = dash.models.Source.objects.filter(source_type__type=dash.constants.SourceType.ADBLADE).first()
        adblade.maintenance = False
        adblade.deprecated = False
        adblade.save()

        ad_group_sources = (
            dash.models.AdGroup.objects.get(pk=1).adgroupsource_set.all().select_related("source", "settings")
        )
        supports_retargeting, sources = dash.retargeting_helper.supports_retargeting(ad_group_sources)
        self.assertTrue(supports_retargeting)
        self.assertEqual(0, len(sources))
