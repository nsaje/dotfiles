import json
import urllib.error
import urllib.parse
import urllib.request

from django.db.models import F
from django.urls import reverse
from mock import patch

import dash.constants
import dash.features.ga
import dash.features.geolocation
import dash.models
from utils import email_helper
from utils import zlogging

from .base_test import K1APIBaseTest

logger = zlogging.getLogger(__name__)
logger.setLevel(zlogging.INFO)


class OutbrainTest(K1APIBaseTest):
    def test_get_publishers_blacklist_outbrain(self):
        response = self.client.get(reverse("k1api.outbrain_publishers_blacklist"), {"marketer_id": "cdefg"})

        data = json.loads(response.content)
        self.assert_response_ok(response, data)
        data = data["response"]

        expected = (
            dash.models.PublisherGroupEntry.objects.filter(publisher_group_id__in=[1000, 11, 12])
            .filter(source__bidder_slug="outbrain")
            .annotate(name=F("publisher"))
            .values("name")
        )
        self.assertGreater(len(expected), 0)
        self.assertEqual(
            data,
            {
                "blacklist": list(expected),
                "account": {"id": 1000, "name": "test outbrain account", "outbrain_marketer_id": "cdefg"},
            },
        )

    def test_get_outbrain_marketer_id(self):
        response = self.client.get(reverse("k1api.outbrain_marketer_id"), {"ad_group_id": "1"})

        data = json.loads(response.content)
        self.assert_response_ok(response, data)

        ag = dash.models.AdGroup.objects.get(pk=1)
        self.assertEqual(ag.campaign.account.outbrain_marketer_id, data["response"])

    def test_sync_outbrain_marketer_new(self):
        self.assertFalse(
            dash.models.OutbrainAccount.objects.filter(marketer_id="abc-456", marketer_name="Abc 456").exists()
        )
        response = self.client.generic(
            "PUT",
            reverse("k1api.outbrain_marketer_sync"),
            QUERY_STRING=urllib.parse.urlencode({"marketer_id": "abc-456", "marketer_name": "Abc 456"}),
        )
        self.assertEqual(
            json.loads(response.content)["response"],
            {"created": True, "marketer_id": "abc-456", "marketer_name": "Abc 456", "used": False},
        )
        self.assertTrue(
            dash.models.OutbrainAccount.objects.filter(marketer_id="abc-456", marketer_name="Abc 456").exists()
        )

    def test_sync_outbrain_marketer_existing(self):
        dash.models.OutbrainAccount.objects.create(marketer_id="abc-123", marketer_name="Abc 123", used=True)
        response = self.client.generic(
            "PUT",
            reverse("k1api.outbrain_marketer_sync"),
            QUERY_STRING=urllib.parse.urlencode({"marketer_id": "abc-123", "marketer_name": "Abc 123"}),
        )
        self.assertEqual(
            json.loads(response.content)["response"],
            {"created": False, "marketer_id": "abc-123", "marketer_name": "Abc 123", "used": True},
        )
        self.assertTrue(
            dash.models.OutbrainAccount.objects.filter(marketer_id="abc-123", marketer_name="Abc 123").exists()
        )

    def test_sync_outbrain_marketer_existing_update_name(self):
        dash.models.OutbrainAccount.objects.create(marketer_id="abc-123", marketer_name="Abc 123", used=True)
        response = self.client.generic(
            "PUT",
            reverse("k1api.outbrain_marketer_sync"),
            QUERY_STRING=urllib.parse.urlencode({"marketer_id": "abc-123", "marketer_name": "New 123"}),
        )
        self.assertEqual(
            json.loads(response.content)["response"],
            {"created": False, "marketer_id": "abc-123", "marketer_name": "New 123", "used": True},
        )
        self.assertTrue(
            dash.models.OutbrainAccount.objects.filter(marketer_id="abc-123", marketer_name="New 123").exists()
        )

    @patch.object(email_helper, "send_internal_email")
    @patch.object(email_helper, "send_outbrain_accounts_running_out_email")
    def test_get_outbrain_marketer_id_assign_new(self, mock_sendmail, mock_sendintentalmail):
        response = self.client.get(reverse("k1api.outbrain_marketer_id"), {"ad_group_id": "3"})

        data = json.loads(response.content)
        self.assert_response_ok(response, data)

        ag = dash.models.AdGroup.objects.get(pk=3)
        self.assertEqual(ag.campaign.account.outbrain_marketer_id, data["response"])
        mock_sendmail.assert_called_with(3)

        acc = ag.campaign.account
        obacc = dash.models.OutbrainAccount.objects.filter(marketer_id=ag.campaign.account.outbrain_marketer_id).last()
        mock_sendintentalmail.assert_called_with(
            recipient_list=["cs@zemanta.com"],
            subject="New Outbrain account / marketer assigned",
            body=f"Assigned new Outbrain marketer {obacc.marketer_name} ({obacc.marketer_id}) for Zemanta Account: {acc.name} ({acc.id}), Agency: {acc.agency.name} ({acc.agency.id})",
        )

    def test_get_outbrain_marketer_id_none_left(self):
        dash.models.OutbrainAccount.objects.all().delete()
        response = self.client.get(reverse("k1api.outbrain_marketer_id"), {"ad_group_id": "3"})
        data = json.loads(response.content)
        self.assertEqual("No unused Outbrain accounts available.", data["error"])
