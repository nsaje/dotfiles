import datetime

from django.urls import reverse
from mock import mock

import core.features.history.models
import core.models
import dash.constants
from restapi.common.views_base_test_case import RESTAPITestCase
from utils.magic_mixer import magic_mixer
from zemauth.features.entity_permission import Permission

from . import constants


class EntityHistoryViewSetTest(RESTAPITestCase):
    def setUp(self):
        super(EntityHistoryViewSetTest, self).setUp()

        # creating these also already creates one history entry
        self.agency = self.mix_agency(self.user, permissions=[Permission.READ, Permission.WRITE])
        self.account = self.mix_account(self.user, permissions=[Permission.READ, Permission.WRITE])
        self.campaign = magic_mixer.blend(core.models.Campaign, account=self.account)
        self.ad_group = magic_mixer.blend(core.models.AdGroup, campaign=self.campaign)

        magic_mixer.blend(
            core.features.history.models.History,
            ad_group=self.ad_group,
            campaign=self.campaign,
            account=self.account,
            agency=self.agency,
            level=dash.constants.HistoryLevel.AD_GROUP,
            changes={"name": "test"},
            changes_text="Name changed to 'test'",
            created_by=self.user,
        )
        magic_mixer.blend(
            core.features.history.models.History,
            campaign=self.campaign,
            account=self.account,
            agency=self.agency,
            level=dash.constants.HistoryLevel.CAMPAIGN,
            changes={"targeting": ["US"]},
            changes_text="Geographic targeting changed to 'US'",
            created_by=self.user,
        )
        magic_mixer.blend(
            core.features.history.models.History,
            account=self.account,
            agency=self.agency,
            level=dash.constants.HistoryLevel.ACCOUNT,
            changes={"account_manager": 1},
            changes_text="Account manager changed to 'Janez Novak'",
            created_by=self.user,
        )
        magic_mixer.blend(
            core.features.history.models.History,
            agency=self.agency,
            level=dash.constants.HistoryLevel.AGENCY,
            changes={"entity_tags": []},
            changes_text="Changed entity tags",
            created_by=self.user,
        )

    def test_get_ad_group_history(self):
        r = self.client.get(
            reverse("restapi.entityhistory.internal:entity_history_details"),
            {
                "ad_group_id": self.ad_group.id,
                "level": dash.constants.HistoryLevel.get_name(dash.constants.HistoryLevel.AD_GROUP),
            },
        )
        resp_json = self.assertResponseValid(r, data_type=list)

        # one history entry is already inserted when the entity was created
        self.assertEqual(2, len(resp_json["data"]))
        self.assertEqual("Name changed to 'test'", resp_json["data"][0]["changesText"])

    def test_get_campaign_history(self):
        r = self.client.get(
            reverse("restapi.entityhistory.internal:entity_history_details"),
            {
                "campaign_id": self.campaign.id,
                "level": dash.constants.HistoryLevel.get_name(dash.constants.HistoryLevel.CAMPAIGN),
            },
        )
        resp_json = self.assertResponseValid(r, data_type=list)

        # one history entry is already inserted when the entity was created
        self.assertEqual(2, len(resp_json["data"]))
        self.assertEqual("Geographic targeting changed to 'US'", resp_json["data"][0]["changesText"])

    def test_get_account_history(self):
        r = self.client.get(
            reverse("restapi.entityhistory.internal:entity_history_details"),
            {
                "account_id": self.account.id,
                "level": dash.constants.HistoryLevel.get_name(dash.constants.HistoryLevel.ACCOUNT),
            },
        )
        resp_json = self.assertResponseValid(r, data_type=list)

        # one history entry is already inserted when the entity was created
        self.assertEqual(2, len(resp_json["data"]))
        self.assertEqual("Account manager changed to 'Janez Novak'", resp_json["data"][0]["changesText"])

    def test_get_agency_history(self):
        r = self.client.get(
            reverse("restapi.entityhistory.internal:entity_history_details"),
            {
                "agency_id": self.agency.id,
                "level": dash.constants.HistoryLevel.get_name(dash.constants.HistoryLevel.AGENCY),
            },
        )
        resp_json = self.assertResponseValid(r, data_type=list)

        # one history entry is already inserted when the entity was created
        self.assertEqual(2, len(resp_json["data"]))
        self.assertEqual("Changed entity tags", resp_json["data"][0]["changesText"])

    def test_get_history_order(self):
        dt = datetime.datetime.utcnow()
        mocked_dt = dt - datetime.timedelta(1)
        with mock.patch("django.utils.timezone.now", mock.Mock(return_value=mocked_dt)):
            magic_mixer.blend(
                core.features.history.models.History,
                account=self.account,
                level=dash.constants.HistoryLevel.ACCOUNT,
                changes={"account_manager": 1},
                changes_text="Account manager changed to 'Janez Novak'",
                created_by=self.user,
            )

        r = self.client.get(
            reverse("restapi.entityhistory.internal:entity_history_details"),
            {
                "account_id": self.account.id,
                "level": dash.constants.HistoryLevel.get_name(dash.constants.HistoryLevel.ACCOUNT),
                "order": constants.EntityHistoryOrder.get_name(constants.EntityHistoryOrder.CREATED_DT_DESC),
            },
        )
        resp_json = self.assertResponseValid(r, data_type=list)

        # one history entry is already inserted when the entity was created
        self.assertEqual(3, len(resp_json["data"]))
        self.assertTrue(resp_json["data"][2]["datetime"] < resp_json["data"][1]["datetime"])

        r = self.client.get(
            reverse("restapi.entityhistory.internal:entity_history_details"),
            {
                "account_id": self.account.id,
                "level": dash.constants.HistoryLevel.get_name(dash.constants.HistoryLevel.ACCOUNT),
                "order": constants.EntityHistoryOrder.get_name(constants.EntityHistoryOrder.CREATED_DT_ASC),
            },
        )
        resp_json = self.assertResponseValid(r, data_type=list)

        # one history entry is already inserted when the entity was created
        self.assertEqual(3, len(resp_json["data"]))
        self.assertTrue(resp_json["data"][2]["datetime"] > resp_json["data"][1]["datetime"])

    def test_get_history_from_date(self):
        dt = datetime.datetime.utcnow()
        mocked_dt = dt - datetime.timedelta(31)
        with mock.patch("django.utils.timezone.now", mock.Mock(return_value=mocked_dt)):
            magic_mixer.blend(
                core.features.history.models.History,
                account=self.account,
                level=dash.constants.HistoryLevel.ACCOUNT,
                changes={"account_manager": 1},
                changes_text="Account manager changed to 'Janez Novak'",
                created_by=self.user,
            )

        r = self.client.get(
            reverse("restapi.entityhistory.internal:entity_history_details"),
            {
                "account_id": self.account.id,
                "level": dash.constants.HistoryLevel.get_name(dash.constants.HistoryLevel.ACCOUNT),
                "from_date": (dt - datetime.timedelta(30)).date(),
            },
        )
        resp_json = self.assertResponseValid(r, data_type=list)

        # one history entry is already inserted when the entity was created
        self.assertEqual(2, len(resp_json["data"]))

    def test_get_invalid_entity(self):
        r = self.client.get(
            reverse("restapi.entityhistory.internal:entity_history_details"),
            {"level": dash.constants.HistoryLevel.get_name(dash.constants.HistoryLevel.AD_GROUP)},
        )
        resp_json = self.assertResponseError(r, "ValidationError")
        self.assertIn(
            "Either ad_group_id, campaign_id, account_id or agency_id must be provided.",
            resp_json["details"]["nonFieldErrors"],
        )
