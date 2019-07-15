import datetime
import decimal

import mock
from django.urls import reverse

import core.models
import dash.constants
import dash.models
import restapi.serializers.targeting
from restapi.common.views_base_test import RESTAPITest
from utils.magic_mixer import magic_mixer


class CampaignViewSetTest(RESTAPITest):
    @classmethod
    def campaign_repr(
        cls,
        id=None,
        account_id=None,
        archived=False,
        autopilot=False,
        iab_category=dash.constants.IABCategory.IAB1_1,
        language=dash.constants.Language.ENGLISH,
        type=dash.constants.CampaignType.CONTENT,
        name="My Campaign TEST",
        enable_ga_tracking=True,
        ga_tracking_type=dash.constants.GATrackingType.EMAIL,
        ga_property_id="",
        enable_adobe_tracking=False,
        adobe_tracking_param="cid",
        whitelist_publisher_groups=[],
        blacklist_publisher_groups=[],
        target_devices=[dash.constants.AdTargetDevice.DESKTOP],
        target_placements=[dash.constants.Placement.APP],
        target_os=[{"name": dash.constants.OperatingSystem.ANDROID}, {"name": dash.constants.OperatingSystem.LINUX}],
        frequency_capping=None,
        campaign_manager=None,
        goals=[],
    ):
        representation = {
            "id": str(id) if id is not None else None,
            "accountId": str(account_id) if account_id is not None else None,
            "archived": archived,
            "autopilot": autopilot,
            "iabCategory": dash.constants.IABCategory.get_name(iab_category),
            "language": dash.constants.Language.get_name(language),
            "type": dash.constants.CampaignType.get_name(type),
            "name": name,
            "tracking": {
                "ga": {
                    "enabled": enable_ga_tracking,
                    "type": dash.constants.GATrackingType.get_name(ga_tracking_type),
                    "webPropertyId": ga_property_id,
                },
                "adobe": {"enabled": enable_adobe_tracking, "trackingParameter": adobe_tracking_param},
            },
            "targeting": {
                "devices": restapi.serializers.targeting.DevicesSerializer(target_devices).data,
                "placements": restapi.serializers.targeting.PlacementsSerializer(target_placements).data,
                "os": restapi.serializers.targeting.OSsSerializer(target_os).data,
                "publisherGroups": {"included": whitelist_publisher_groups, "excluded": blacklist_publisher_groups},
            },
            "frequencyCapping": frequency_capping,
            "campaignManager": campaign_manager,
            "goals": goals,
        }
        return cls.normalize(representation)

    @classmethod
    def campaign_goal_repr(
        cls,
        id=None,
        primary=True,
        type=dash.constants.CampaignGoalKPI.TIME_ON_SITE,
        conversion_goal=None,
        value="30.0000",
    ):
        representation = {
            "id": id,
            "primary": primary,
            "type": dash.constants.CampaignGoalKPI.get_name(type),
            "conversionGoal": conversion_goal,
            "value": value,
        }
        return cls.normalize(representation)

    @classmethod
    def campaign_budget_repr(cls, budget=None):
        if budget is None:
            return None

        representation = {
            "id": str(budget.id),
            "creditId": str(budget.credit.id),
            "amount": str(budget.amount),
            "margin": str(budget.margin),
            "comment": budget.comment,
            "startDate": budget.start_date,
            "endDate": budget.end_date,
            "state": dash.constants.BudgetLineItemState.get_name(budget.state()),
            "spend": budget.get_local_spend_data_bcm(),
            "available": budget.get_local_available_data_bcm(),
            "canEditStartDate": budget.can_edit_start_date(),
            "canEditEndDate": budget.can_edit_end_date(),
            "canEditAmount": budget.can_edit_amount(),
            "createdBy": str(budget.created_by),
            "createdDt": budget.created_dt,
            "licenseFee": budget.credit.license_fee,
        }
        return cls.normalize(representation)

    @classmethod
    def credit_item_repr(cls, credit_item=None):
        if credit_item is None:
            return None

        representation = {
            "id": str(credit_item.pk),
            "total": str(credit_item.effective_amount()),
            "allocated": str(credit_item.get_allocated_amount()),
            "available": str(credit_item.get_available_amount()),
            "createdOn": credit_item.get_creation_date(),
            "startDate": credit_item.start_date,
            "endDate": credit_item.end_date,
            "comment": credit_item.comment,
            "status": dash.constants.CreditLineItemStatus.get_name(credit_item.status),
            "currency": dash.constants.Currency.get_name(credit_item.currency),
            "isAvailable": credit_item.is_available(),
            "isAgency": credit_item.is_agency(),
            "licenseFee": str(credit_item.license_fee),
        }
        return cls.normalize(representation)

    def test_validate_empty(self):
        r = self.client.post(reverse("restapi.campaign.internal:campaigns_validate"))
        self.assertResponseValid(r, data_type=type(None))

    def test_validate(self):
        data = {"name": "New campaign", "accountId": 123}
        r = self.client.post(reverse("restapi.campaign.internal:campaigns_validate"), data=data, format="json")
        self.assertResponseValid(r, data_type=type(None))

    def test_validate_error(self):
        data = {"name": None, "accountId": None}
        r = self.client.post(reverse("restapi.campaign.internal:campaigns_validate"), data=data, format="json")
        r = self.assertResponseError(r, "ValidationError")
        self.assertIn("This field may not be null.", r["details"]["name"][0])
        self.assertIn("This field may not be null.", r["details"]["accountId"][0])

    @mock.patch("restapi.campaign.internal.helpers.get_extra_data")
    def test_get_default(self, mock_get_extra_data):
        mock_get_extra_data.return_value = {
            "archived": False,
            "language": dash.constants.Language.ENGLISH,
            "can_archive": True,
            "can_restore": True,
            "currency": dash.constants.Currency.USD,
            "goals_defaults": {
                dash.constants.CampaignGoalKPI.TIME_ON_SITE: "30.00",
                dash.constants.CampaignGoalKPI.MAX_BOUNCE_RATE: "75.00",
            },
            "campaign_managers": [
                {"id": 123, "name": "manager1@outbrain.com"},
                {"id": 123, "name": "manager2@outbrain.com"},
            ],
            "hacks": [],
            "deals": [],
            "budgets_overview": {
                "available_budgets_sum": decimal.Decimal("0.0000"),
                "unallocated_credit": decimal.Decimal("0.0000"),
                "campaign_spend": decimal.Decimal("0.0000"),
                "margin": decimal.Decimal("0.0000"),
            },
            "budgets_depleted": [],
            "available_credits": [],
        }

        agency = magic_mixer.blend(core.models.Agency)
        account = magic_mixer.blend(core.models.Account, agency=agency, users=[self.user])

        r = self.client.get(reverse("restapi.campaign.internal:campaigns_defaults"), {"accountId": account.id})
        resp_json = self.assertResponseValid(r)

        self.assertEqual(resp_json["data"]["name"], "New campaign")
        self.assertEqual(resp_json["data"]["accountId"], str(account.id))
        self.assertEqual(
            resp_json["data"]["type"], dash.constants.CampaignType.get_name(dash.constants.CampaignType.CONTENT)
        )
        self.assertEqual(
            resp_json["data"]["language"], dash.constants.Language.get_name(dash.constants.Language.ENGLISH)
        )
        self.assertEqual(resp_json["data"]["autopilot"], True)
        self.assertEqual(
            resp_json["data"]["iabCategory"], dash.constants.IABCategory.get_name(dash.constants.IABCategory.IAB24)
        )
        self.assertEqual(resp_json["data"]["campaignManager"], self.user.id)
        self.assertEqual(resp_json["data"]["goals"], [])
        self.assertEqual(
            resp_json["extra"],
            {
                "archived": False,
                "language": dash.constants.Language.get_name(dash.constants.Language.ENGLISH),
                "canArchive": True,
                "canRestore": True,
                "currency": dash.constants.Currency.get_name(dash.constants.Currency.USD),
                "goalsDefaults": {
                    dash.constants.CampaignGoalKPI.get_name(dash.constants.CampaignGoalKPI.TIME_ON_SITE): "30.00",
                    dash.constants.CampaignGoalKPI.get_name(dash.constants.CampaignGoalKPI.MAX_BOUNCE_RATE): "75.00",
                },
                "campaignManagers": [
                    {"id": 123, "name": "manager1@outbrain.com"},
                    {"id": 123, "name": "manager2@outbrain.com"},
                ],
                "hacks": [],
                "deals": [],
                "budgetsOverview": {
                    "availableBudgetsSum": "0.0000",
                    "unallocatedCredit": "0.0000",
                    "campaignSpend": "0.0000",
                    "margin": "0.0000",
                },
                "budgetsDepleted": [],
                "availableCredits": [],
            },
        )

    @mock.patch("restapi.campaign.internal.helpers.get_extra_data")
    def test_get(self, mock_get_extra_data):
        agency = magic_mixer.blend(core.models.Agency)
        account = magic_mixer.blend(core.models.Account, agency=agency, users=[self.user])
        campaign = magic_mixer.blend(
            core.models.Campaign, account=account, name="Test campaign", type=dash.constants.CampaignType.CONTENT
        )
        campaign.settings.update_unsafe(
            None,
            name=campaign.name,
            language=dash.constants.Language.ENGLISH,
            autopilot=True,
            iab_category=dash.constants.IABCategory.IAB24,
            campaign_manager=self.user,
        )

        conversion_goal = magic_mixer.blend(
            dash.models.ConversionGoal,
            campaign=campaign,
            name="Conversion goal name",
            type=dash.constants.ConversionGoalType.GA,
            goal_id="GA_123_TEST",
            pixel=None,
            conversion_window=dash.constants.ConversionWindows.LEQ_1_DAY,
        )
        campaign_goal = magic_mixer.blend(
            dash.models.CampaignGoal,
            campaign=campaign,
            type=dash.constants.CampaignGoalKPI.CPA,
            conversion_goal=conversion_goal,
            primary=True,
        )
        campaign_goal.add_local_value(None, decimal.Decimal("0.15"), skip_history=True)

        credit = magic_mixer.blend(
            dash.models.CreditLineItem,
            account=account,
            start_date=datetime.date.today() - datetime.timedelta(30),
            end_date=datetime.date.today() + datetime.timedelta(30),
            amount=200000,
            currency=dash.constants.Currency.USD,
            status=dash.constants.CreditLineItemStatus.SIGNED,
        )
        inactive_budget = magic_mixer.blend(
            dash.models.BudgetLineItem,
            campaign=campaign,
            credit=credit,
            start_date=datetime.date.today() - datetime.timedelta(20),
            end_date=datetime.date.today() - datetime.timedelta(5),
            created_by=self.user,
            amount=10000,
            margin=decimal.Decimal("0.2500"),
        )

        mock_get_extra_data.return_value = {
            "archived": False,
            "language": dash.constants.Language.ENGLISH,
            "can_archive": True,
            "can_restore": True,
            "currency": dash.constants.Currency.USD,
            "goals_defaults": {
                dash.constants.CampaignGoalKPI.TIME_ON_SITE: "30.00",
                dash.constants.CampaignGoalKPI.MAX_BOUNCE_RATE: "75.00",
            },
            "campaign_managers": [
                {"id": 123, "name": "manager1@outbrain.com"},
                {"id": 123, "name": "manager2@outbrain.com"},
            ],
            "hacks": [],
            "deals": [],
            "budgets_overview": {
                "available_budgets_sum": decimal.Decimal("10.0000"),
                "unallocated_credit": decimal.Decimal("10.0000"),
                "campaign_spend": decimal.Decimal("10.0000"),
                "media_spend": decimal.Decimal("220.0000"),
                "data_spend": decimal.Decimal("100.0000"),
                "license_fee": decimal.Decimal("5.0000"),
                "margin": decimal.Decimal("2.0000"),
            },
            "budgets_depleted": [inactive_budget],
            "available_credits": [credit],
        }

        r = self.client.get(reverse("restapi.campaign.internal:campaigns_details", kwargs={"campaign_id": campaign.id}))
        resp_json = self.assertResponseValid(r)

        self.assertEqual(resp_json["data"]["name"], campaign.get_current_settings().name)
        self.assertEqual(resp_json["data"]["accountId"], str(account.id))
        self.assertEqual(resp_json["data"]["type"], dash.constants.CampaignType.get_name(campaign.type))
        self.assertEqual(
            resp_json["data"]["language"], dash.constants.Language.get_name(campaign.get_current_settings().language)
        )
        self.assertEqual(resp_json["data"]["autopilot"], campaign.get_current_settings().autopilot)
        self.assertEqual(
            resp_json["data"]["iabCategory"],
            dash.constants.IABCategory.get_name(campaign.get_current_settings().iab_category),
        )
        self.assertEqual(resp_json["data"]["campaignManager"], campaign.get_current_settings().campaign_manager.id)
        self.assertEqual(len(resp_json["data"]["goals"]), 1)
        self.assertEqual(
            resp_json["data"]["goals"],
            [
                {
                    "id": campaign_goal.id,
                    "primary": campaign_goal.primary,
                    "type": dash.constants.CampaignGoalKPI.get_name(campaign_goal.type),
                    "conversionGoal": {
                        "goalId": conversion_goal.goal_id,
                        "name": conversion_goal.name,
                        "pixelUrl": None,
                        "conversionWindow": dash.constants.ConversionWindows.get_name(
                            conversion_goal.conversion_window
                        ),
                        "type": dash.constants.ConversionGoalType.get_name(conversion_goal.type),
                    },
                    "value": str(campaign_goal.get_current_value().local_value.quantize(decimal.Decimal("1.00"))),
                }
            ],
        )
        self.assertEqual(
            resp_json["extra"],
            {
                "archived": False,
                "language": dash.constants.Language.get_name(dash.constants.Language.ENGLISH),
                "canArchive": True,
                "canRestore": True,
                "currency": dash.constants.Currency.get_name(dash.constants.Currency.USD),
                "goalsDefaults": {
                    dash.constants.CampaignGoalKPI.get_name(dash.constants.CampaignGoalKPI.TIME_ON_SITE): "30.00",
                    dash.constants.CampaignGoalKPI.get_name(dash.constants.CampaignGoalKPI.MAX_BOUNCE_RATE): "75.00",
                },
                "campaignManagers": [
                    {"id": 123, "name": "manager1@outbrain.com"},
                    {"id": 123, "name": "manager2@outbrain.com"},
                ],
                "hacks": [],
                "deals": [],
                "budgetsOverview": {
                    "availableBudgetsSum": "10.0000",
                    "unallocatedCredit": "10.0000",
                    "campaignSpend": "10.0000",
                    "mediaSpend": "220.0000",
                    "dataSpend": "100.0000",
                    "licenseFee": "5.0000",
                    "margin": "2.0000",
                },
                "budgetsDepleted": [self.campaign_budget_repr(inactive_budget)],
                "availableCredits": [self.credit_item_repr(credit)],
            },
        )

    @mock.patch("automation.autopilot.recalculate_budgets_campaign")
    @mock.patch("utils.email_helper.send_campaign_created_email")
    def test_post(self, mock_send, mock_autopilot):
        agency = magic_mixer.blend(core.models.Agency)
        account = magic_mixer.blend(core.models.Account, agency=agency, users=[self.user])

        campaign_goal_time_on_site = self.campaign_goal_repr(
            type=dash.constants.CampaignGoalKPI.TIME_ON_SITE, primary=True
        )
        campaign_goal_new_unique_visitors = self.campaign_goal_repr(
            type=dash.constants.CampaignGoalKPI.NEW_UNIQUE_VISITORS, primary=False
        )

        new_campaign = self.campaign_repr(
            account_id=account.id,
            campaign_manager=self.user.id,
            goals=[campaign_goal_time_on_site, campaign_goal_new_unique_visitors],
        )

        r = self.client.post(reverse("restapi.campaign.internal:campaigns_list"), data=new_campaign, format="json")
        resp_json = self.assertResponseValid(r, data_type=dict, status_code=201)

        self.assertEqual(resp_json["data"]["name"], new_campaign["name"])
        self.assertEqual(resp_json["data"]["accountId"], str(account.id))
        self.assertEqual(resp_json["data"]["type"], new_campaign["type"])
        self.assertEqual(resp_json["data"]["language"], new_campaign["language"])
        self.assertEqual(resp_json["data"]["iabCategory"], new_campaign["iabCategory"])
        self.assertEqual(resp_json["data"]["campaignManager"], new_campaign["campaignManager"])
        self.assertEqual(len(resp_json["data"]["goals"]), 2)
        self.assertIsNotNone(resp_json["data"]["goals"][0]["id"])
        self.assertEqual(
            resp_json["data"]["goals"][0]["type"],
            dash.constants.CampaignGoalKPI.get_name(dash.constants.CampaignGoalKPI.TIME_ON_SITE),
        )
        self.assertEqual(resp_json["data"]["goals"][0]["primary"], True)
        self.assertIsNotNone(resp_json["data"]["goals"][1]["id"])
        self.assertEqual(resp_json["data"]["goals"][1]["primary"], False)
        self.assertEqual(
            resp_json["data"]["goals"][1]["type"],
            dash.constants.CampaignGoalKPI.get_name(dash.constants.CampaignGoalKPI.NEW_UNIQUE_VISITORS),
        )

    def test_post_campaign_manager_error(self):
        agency = magic_mixer.blend(core.models.Agency)
        account = magic_mixer.blend(core.models.Account, agency=agency, users=[self.user])

        new_campaign = self.campaign_repr(account_id=account.id, campaign_manager=904324)

        r = self.client.post(reverse("restapi.campaign.internal:campaigns_list"), data=new_campaign, format="json")
        r = self.assertResponseError(r, "ValidationError")

        self.assertIn("Invalid campaign manager.", r["details"]["campaignManager"][0])

    @mock.patch("automation.autopilot.recalculate_budgets_campaign")
    @mock.patch("utils.email_helper.send_campaign_created_email")
    def test_post_goals_error(self, mock_send, mock_autopilot):
        agency = magic_mixer.blend(core.models.Agency)
        account = magic_mixer.blend(core.models.Account, agency=agency, users=[self.user])

        new_campaign = self.campaign_repr(account_id=account.id, campaign_manager=self.user.id, goals=[])

        r = self.client.post(reverse("restapi.campaign.internal:campaigns_list"), data=new_campaign, format="json")
        r = self.assertResponseError(r, "ValidationError")

        self.assertIn("At least one goal must be defined.", r["details"]["goalsMissing"][0])

    @mock.patch("automation.autopilot.recalculate_budgets_campaign")
    @mock.patch("utils.email_helper.send_campaign_created_email")
    def test_put(self, mock_send, mock_autopilot):
        agency = magic_mixer.blend(core.models.Agency)
        account = magic_mixer.blend(core.models.Account, agency=agency, users=[self.user])
        campaign = magic_mixer.blend(
            core.models.Campaign, account=account, name="Test campaign", type=dash.constants.CampaignType.CONTENT
        )
        campaign.settings.update_unsafe(
            None,
            name=campaign.name,
            language=dash.constants.Language.ENGLISH,
            autopilot=True,
            iab_category=dash.constants.IABCategory.IAB24,
            campaign_manager=self.user,
        )

        conversion_goal = magic_mixer.blend(
            dash.models.ConversionGoal,
            campaign=campaign,
            name="Conversion goal name",
            type=dash.constants.ConversionGoalType.GA,
            goal_id="GA_123_TEST",
            pixel=None,
            conversion_window=dash.constants.ConversionWindows.LEQ_1_DAY,
        )
        campaign_goal = magic_mixer.blend(
            dash.models.CampaignGoal,
            campaign=campaign,
            type=dash.constants.CampaignGoalKPI.CPA,
            conversion_goal=conversion_goal,
            primary=True,
        )
        campaign_goal.add_local_value(None, decimal.Decimal("0.15"), skip_history=True)

        r = self.client.get(reverse("restapi.campaign.internal:campaigns_details", kwargs={"campaign_id": campaign.id}))
        resp_json = self.assertResponseValid(r)

        self.assertEqual(len(resp_json["data"]["goals"]), 1)

        put_data = resp_json["data"].copy()

        put_data["campaignManager"] = self.user.id
        put_data["goals"][0]["primary"] = False

        campaign_goal_time_on_site = self.campaign_goal_repr(
            type=dash.constants.CampaignGoalKPI.TIME_ON_SITE, primary=True
        )
        campaign_goal_new_unique_visitors = self.campaign_goal_repr(
            type=dash.constants.CampaignGoalKPI.NEW_UNIQUE_VISITORS, primary=False
        )

        put_data["goals"].append(campaign_goal_time_on_site)
        put_data["goals"].append(campaign_goal_new_unique_visitors)

        r = self.client.put(
            reverse("restapi.campaign.internal:campaigns_details", kwargs={"campaign_id": campaign.id}),
            data=put_data,
            format="json",
        )
        resp_json = self.assertResponseValid(r)

        self.assertEqual(resp_json["data"]["campaignManager"], self.user.id)
        self.assertEqual(len(resp_json["data"]["goals"]), 3)

        self.assertIsNotNone(resp_json["data"]["goals"][0]["id"])
        self.assertEqual(
            resp_json["data"]["goals"][0]["type"], dash.constants.CampaignGoalKPI.get_name(campaign_goal.type)
        )
        self.assertEqual(resp_json["data"]["goals"][0]["primary"], False)

        self.assertIsNotNone(resp_json["data"]["goals"][1]["id"])
        self.assertEqual(
            resp_json["data"]["goals"][1]["type"],
            dash.constants.CampaignGoalKPI.get_name(dash.constants.CampaignGoalKPI.TIME_ON_SITE),
        )
        self.assertEqual(resp_json["data"]["goals"][1]["primary"], True)

        self.assertIsNotNone(resp_json["data"]["goals"][2]["id"])
        self.assertEqual(
            resp_json["data"]["goals"][2]["type"],
            dash.constants.CampaignGoalKPI.get_name(dash.constants.CampaignGoalKPI.NEW_UNIQUE_VISITORS),
        )
        self.assertEqual(resp_json["data"]["goals"][2]["primary"], False)
