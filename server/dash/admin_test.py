import mock

from django.core import urlresolvers
from django.contrib.admin.sites import AdminSite
from django.test import TestCase
from django.http.request import HttpRequest

from dash import models
from dash import constants
from dash import admin
from zemauth.models import User


class SourceAdminTestCase(TestCase):

    fixtures = ['test_models']

    def setUp(self):
        password = 'secret'
        user = User.objects.get(pk=1)
        self.request = HttpRequest()
        self.request.user = user
        self.client.login(username=user.email, password=password)

    def test_deprecate_selected(self):
        change_url = urlresolvers.reverse('admin:dash_source_changelist')
        response = self.client.post(change_url, {'action': 'deprecate_selected', '_selected_action': 1}, follow=True)
        self.assertEqual(response.status_code, 200)

        source = models.Source.objects.get(pk=1)
        ad_group_sources = models.AdGroupSource.objects.filter(source=source)
        for ad_group_source in ad_group_sources:
            settings = ad_group_source.get_current_settings()
            self.assertEqual(settings.state, constants.AdGroupSourceSettingsState.INACTIVE)


class AdGroupAdmin(TestCase):

    fixtures = ['test_models']

    @mock.patch.object(admin.utils.redirector_helper, 'insert_adgroup')
    def test_save_additional_targeting(self, mock_r1_insert_adgroup):
        trackers = ['http://a.com', 'http://b.com']
        javascript = 'alert("A");'
        interest_targeting = ['segment1', 'segment2']

        ad_group = models.AdGroup.objects.get(pk=1)

        adgroup_admin = admin.AdGroupAdmin(models.AdGroup, AdminSite())

        request = mock.Mock()
        request.user = User.objects.get(pk=1)

        form = adgroup_admin.get_form(request)()
        form.cleaned_data = {}
        for field in form.SETTINGS_FIELDS:
            form.cleaned_data[field] = getattr(ad_group.settings, field)

        form.cleaned_data['notes'] = 'new notes'
        adgroup_admin.save_model(request, ad_group, form, None)
        old_settings = models.AdGroupSettings.objects.filter(ad_group=ad_group)[1]
        self.assertNotEqual(old_settings.notes, 'new notes')
        self.assertEqual(ad_group.settings.notes, 'new notes')
        mock_r1_insert_adgroup.assert_not_called()

        form.cleaned_data['redirect_pixel_urls'] = trackers
        form.cleaned_data['redirect_javascript'] = javascript
        form.cleaned_data['interest_targeting'] = interest_targeting
        form.cleaned_data['exclusion_interest_targeting'] = interest_targeting
        adgroup_admin.save_model(request, ad_group, form, None)
        old_settings = models.AdGroupSettings.objects.filter(ad_group=ad_group)[1]
        self.assertNotEqual(old_settings.redirect_pixel_urls, trackers)
        self.assertNotEqual(old_settings.redirect_javascript, javascript)
        self.assertEqual(ad_group.settings.redirect_pixel_urls, trackers)
        self.assertEqual(ad_group.settings.redirect_javascript, javascript)
        self.assertEqual(ad_group.settings.interest_targeting, interest_targeting)
        mock_r1_insert_adgroup.assert_called_with(ad_group)
