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

    @mock.patch.object(admin.AdGroupAdmin, '_handle_manual_interest_targeting_action')
    @mock.patch.object(admin.utils.redirector_helper, 'insert_adgroup')
    def test_save_additional_targeting(self, mock_r1_insert_adgroup, mock_handle_manual):
        trackers = ['http://a.com', 'http://b.com']
        javascript = 'alert("A");'
        interest_targeting = ['segment1', 'segment2']

        ad_group = models.AdGroup.objects.get(pk=1)
        old_settings = ad_group.get_current_settings()

        adgroup_admin = admin.AdGroupAdmin(models.AdGroup, AdminSite())

        request = mock.Mock()
        request.user = User.objects.get(pk=1)

        form = adgroup_admin.get_form(request)()
        form.cleaned_data = {}
        for field in form.SETTINGS_FIELDS:
            form.cleaned_data[field] = getattr(old_settings, field)

        form.cleaned_data['notes'] = 'new notes'
        adgroup_admin.save_model(request, ad_group, form, None)
        new_settings = ad_group.get_current_settings()
        self.assertNotEqual(old_settings.notes, 'new notes')
        self.assertEqual(new_settings.notes, 'new notes')
        mock_r1_insert_adgroup.assert_not_called()

        old_settings = ad_group.get_current_settings()
        form.cleaned_data['redirect_pixel_urls'] = trackers
        form.cleaned_data['redirect_javascript'] = javascript
        form.cleaned_data['interest_targeting'] = interest_targeting
        form.cleaned_data['exclusion_interest_targeting'] = interest_targeting
        adgroup_admin.save_model(request, ad_group, form, None)
        new_settings = ad_group.get_current_settings()
        self.assertNotEqual(old_settings.redirect_pixel_urls, trackers)
        self.assertNotEqual(old_settings.redirect_javascript, javascript)
        self.assertEqual(new_settings.redirect_pixel_urls, trackers)
        self.assertEqual(new_settings.redirect_javascript, javascript)
        self.assertEqual(new_settings.interest_targeting, interest_targeting)
        mock_r1_insert_adgroup.assert_called_with(
            ad_group.id,
            old_settings.get_tracking_codes(),
            old_settings.enable_ga_tracking,
            old_settings.enable_adobe_tracking,
            old_settings.adobe_tracking_param,
            trackers,
            javascript
        )
        self.assertEqual(mock_handle_manual.call_count, 6)

    @mock.patch.object(admin.actionlog.api, 'init_set_ad_group_manual_property')
    def test_handle_manual_interest_targeting_action(self, mock_actionlog_init_manual):
        ad_group = models.AdGroup.objects.get(pk=1)
        current_settings = ad_group.get_current_settings()
        new_settings = current_settings.copy_settings()
        new_settings.interest_targeting = ['new', 'targeting']
        new_settings.exclusion_interest_targeting = ['new', 'targeting']
        admin.AdGroupAdmin._handle_manual_interest_targeting_action(
            mock.Mock(), ad_group, 'adiant', current_settings, new_settings)
        self.assertEqual(mock_actionlog_init_manual.call_count, 2)
