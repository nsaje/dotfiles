import mock
from django.contrib.admin.sites import AdminSite
from django.core.exceptions import ValidationError
from django.test import TestCase

import core.models
from dash import admin
from dash import forms
from dash import models
from utils.magic_mixer import magic_mixer
from zemauth.models import User


class AdGroupAdmin(TestCase):

    fixtures = ["test_models"]

    @mock.patch.object(admin.utils.redirector_helper, "insert_adgroup")
    def test_save_additional_targeting(self, mock_r1_insert_adgroup):
        trackers = ["http://a.com", "http://b.com"]
        javascript = 'alert("A");'

        ad_group = models.AdGroup.objects.get(pk=1)

        adgroup_admin = admin.AdGroupAdmin(models.AdGroup, AdminSite())

        request = mock.Mock()
        request.user = User.objects.get(pk=1)

        form = adgroup_admin.get_form(request)()
        form.cleaned_data = {}
        for field in form.SETTINGS_FIELDS:
            form.cleaned_data[field] = getattr(ad_group.settings, field)

        form.cleaned_data["notes"] = "new notes"
        adgroup_admin.save_model(request, ad_group, form, None)
        old_settings = models.AdGroupSettings.objects.filter(ad_group=ad_group)[1]
        self.assertNotEqual(old_settings.notes, "new notes")
        self.assertEqual(ad_group.settings.notes, "new notes")
        mock_r1_insert_adgroup.assert_not_called()

        form.cleaned_data["redirect_pixel_urls"] = trackers
        form.cleaned_data["redirect_javascript"] = javascript
        adgroup_admin.save_model(request, ad_group, form, None)
        old_settings = models.AdGroupSettings.objects.filter(ad_group=ad_group)[1]
        self.assertNotEqual(old_settings.redirect_pixel_urls, trackers)
        self.assertNotEqual(old_settings.redirect_javascript, javascript)
        self.assertEqual(ad_group.settings.redirect_pixel_urls, trackers)
        self.assertEqual(ad_group.settings.redirect_javascript, javascript)
        mock_r1_insert_adgroup.assert_called_with(ad_group)


class DirectDealConnectionAdminTestCase(TestCase):
    def setUp(self):
        self.source = magic_mixer.blend(core.models.Source, pk=1, bidder_slug="test_exchange_1")
        self.deal1 = magic_mixer.blend(core.features.deals.DirectDeal, deal_id="test_1", source=self.source)
        self.deal2 = magic_mixer.blend(core.features.deals.DirectDeal, deal_id="test_2", source=self.source)
        self.adgroup = magic_mixer.blend(core.models.AdGroup, pk=1000)
        self.agency = magic_mixer.blend(core.models.Agency, pk=2000)
        self.ddc = magic_mixer.blend(core.features.deals.DirectDealConnection, pk=1, deal=self.deal1)
        self.ddc.save()

    def test_clean_everything_ok(self):
        direct_deal_connection_admin = admin.DirectDealAdmin(models.DirectDealConnection, AdminSite())
        direct_deal_connection_admin.form = forms.DirectDealConnectionAdminForm

        form = direct_deal_connection_admin.get_form(None)({})
        form.cleaned_data = {"exclusive": False}

        form.cleaned_data["deal"] = core.features.deals.DirectDeal.objects.filter(deal_id="test_2").all()

        # adgroup
        form.cleaned_data["adgroup"] = self.adgroup
        try:
            form.clean()
        except Exception as e:
            self.fail("raised Exception unexpectedly!: " + e.message)

        # agency
        del form.cleaned_data["adgroup"]
        form.cleaned_data["agency"] = self.agency
        try:
            form.clean()
        except Exception as e:
            self.fail("raised Exception unexpectedly!: " + e.message)

    def test_clean_deals_required(self):
        direct_deal_connection_admin = admin.DirectDealAdmin(models.DirectDealConnection, AdminSite())
        direct_deal_connection_admin.form = forms.DirectDealConnectionAdminForm

        form = direct_deal_connection_admin.get_form(None)()
        form.cleaned_data = {"exclusive": False}

        try:
            form.clean()
        except ValidationError as e:
            self.assertTrue("Deal is required!" in e.message)

    def test_clean_deal_already_used_as_global_deal(self):
        direct_deal_connection_admin = admin.DirectDealAdmin(models.DirectDealConnection, AdminSite())
        direct_deal_connection_admin.form = forms.DirectDealConnectionAdminForm

        form = direct_deal_connection_admin.get_form(None)()
        form.cleaned_data = {"exclusive": False}

        form.cleaned_data["deal"] = core.features.deals.DirectDeal.objects.filter(deal_id="test_1").all()

        # adgroup
        form.cleaned_data["adgroup"] = self.adgroup
        try:
            form.clean()
        except ValidationError as e:
            self.assertTrue("Deal test_1 is already used as global deal" in e.message)

        # agency
        del form.cleaned_data["adgroup"]
        form.cleaned_data["agency"] = self.agency
        try:
            form.clean()
        except ValidationError as e:
            self.assertTrue("Deal test_1 is already used as global deal" in e.message)

    def test_clean_adgroup_and_agency_selected(self):
        direct_deal_connection_admin = admin.DirectDealAdmin(models.DirectDealConnection, AdminSite())
        direct_deal_connection_admin.form = forms.DirectDealConnectionAdminForm
        form = direct_deal_connection_admin.get_form(None)()
        form.cleaned_data = {"exclusive": False}

        form.cleaned_data["deal"] = core.features.deals.DirectDeal.objects.filter(deal_id="test_2").all()

        form.cleaned_data["adgroup"] = self.adgroup
        form.cleaned_data["agency"] = self.agency

        try:
            form.clean()
        except ValidationError as e:
            self.assertTrue("Configuring both agency and adgroup is not allowed" in e.message)

    def test_clean_exclusive_flag_for_global_deal(self):
        direct_deal_connection_admin = admin.DirectDealAdmin(models.DirectDealConnection, AdminSite())
        direct_deal_connection_admin.form = forms.DirectDealConnectionAdminForm

        form = direct_deal_connection_admin.get_form(None)()
        form.cleaned_data = {"exclusive": True}

        form.cleaned_data["deal"] = core.features.deals.DirectDeal.objects.filter(deal_id="test_2").all()

        try:
            form.clean()
        except ValidationError as e:
            self.assertTrue("Exclusive flag can be True only in combination with agency or adgroup" in e.message)
