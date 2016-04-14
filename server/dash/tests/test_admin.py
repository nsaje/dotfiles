from django.core import urlresolvers
from django.test import TestCase
from django.http.request import HttpRequest

from dash import models
from dash import constants
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
        response = self.client.post(change_url, {'action': 'deprecate_selected', '_selected_action': 1})
        self.assertEqual(response.status_code, 200)

        source = models.Source.objects.get(pk=1)
        ad_group_sources = models.AdGroupSource.objects.filter(source=source)
        for ad_group_source in ad_group_sources:
            settings = ad_group_source.get_current_settings()
            self.assertEqual(settings.state, constants.AdGroupSourceSettingsState.INACTIVE)
