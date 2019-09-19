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
        budgets=[],
        deals=[],
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
            "budgets": budgets,
            "deals": deals,
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
            "id": id if id is not None else None,
            "primary": primary,
            "type": dash.constants.CampaignGoalKPI.get_name(type),
            "conversionGoal": conversion_goal,
            "value": value,
        }
        return cls.normalize(representation)

    @classmethod
    def campaign_budget_repr(
        cls,
        id=None,
        creditId=None,
        amount=None,
        margin=None,
        comment=None,
        startDate=None,
        endDate=None,
        state=dash.constants.BudgetLineItemState.PENDING,
        spend=None,
        available=None,
        canEditStartDate=None,
        canEditEndDate=None,
        canEditAmount=None,
        createdBy=None,
        createdDt=None,
        licenseFee=None,
    ):
        representation = {
            "id": str(id) if id is not None else None,
            "creditId": str(creditId) if creditId is not None else None,
            "amount": str(amount) if amount is not None else None,
            "margin": str(margin) if margin is not None else None,
            "comment": comment if comment is not None else "",
            "startDate": startDate,
            "endDate": endDate,
            "state": dash.constants.BudgetLineItemState.get_name(state),
            "spend": str(spend),
            "available": str(available),
            "canEditStartDate": canEditStartDate,
            "canEditEndDate": canEditEndDate,
            "canEditAmount": canEditAmount,
            "createdBy": str(createdBy),
            "createdDt": createdDt,
            "licenseFee": licenseFee,
        }
        return cls.normalize(representation)

    @classmethod
    def credit_item_repr(
        cls,
        id=None,
        totalAmount=None,
        allocatedAmount=None,
        availableAmount=None,
        createdOn=None,
        startDate=None,
        endDate=None,
        comment=None,
        status=None,
        currency=dash.constants.Currency.USD,
        isAvailable=None,
        isAgency=None,
        licenseFee=None,
    ):
        representation = {
            "id": str(id) if id is not None else None,
            "total": str(totalAmount),
            "allocated": str(allocatedAmount),
            "available": str(availableAmount),
            "createdOn": createdOn,
            "startDate": startDate,
            "endDate": endDate,
            "comment": comment,
            "status": dash.constants.CreditLineItemStatus.get_name(status),
            "currency": dash.constants.Currency.get_name(currency),
            "isAvailable": isAvailable,
            "isAgency": isAgency,
            "licenseFee": str(licenseFee),
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
                {"id": 456, "name": "manager2@outbrain.com"},
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
            "account_credits": [],
        }

        agency = magic_mixer.blend(core.models.Agency)
        account = magic_mixer.blend(core.models.Account, agency=agency, users=[self.user])

        r = self.client.get(reverse("restapi.campaign.internal:campaigns_defaults"), {"accountId": account.id})
        resp_json = self.assertResponseValid(r)

        self.assertIsNone(resp_json["data"]["id"])
        self.assertEqual(resp_json["data"]["name"], "")
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
        self.assertEqual(resp_json["data"]["campaignManager"], str(self.user.id))
        self.assertEqual(resp_json["data"]["goals"], [])
        self.assertEqual(resp_json["data"]["budgets"], [])
        self.assertEqual(resp_json["data"]["deals"], [])

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
                    {"id": "123", "name": "manager1@outbrain.com"},
                    {"id": "456", "name": "manager2@outbrain.com"},
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
                "accountCredits": [],
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
        active_budget = magic_mixer.blend(
            dash.models.BudgetLineItem,
            campaign=campaign,
            credit=credit,
            start_date=datetime.date.today() - datetime.timedelta(1),
            end_date=datetime.date.today() + datetime.timedelta(5),
            created_by=self.user,
            amount=10000,
            margin=decimal.Decimal("0.2500"),
        )

        source = magic_mixer.blend(core.models.Source, released=True, deprecated=False)
        deal = magic_mixer.blend(core.features.deals.DirectDeal, agency=agency, source=source)
        magic_mixer.blend(core.features.deals.DirectDealConnection, deal=deal, campaign=campaign)

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
                {"id": 456, "name": "manager2@outbrain.com"},
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
            "account_credits": [credit],
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
        self.assertEqual(resp_json["data"]["campaignManager"], str(campaign.get_current_settings().campaign_manager.id))
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
            resp_json["data"]["budgets"],
            [
                self.campaign_budget_repr(
                    id=active_budget.id,
                    creditId=active_budget.credit.id,
                    amount=active_budget.amount,
                    margin=active_budget.margin,
                    comment=active_budget.comment,
                    startDate=active_budget.start_date,
                    endDate=active_budget.end_date,
                    state=active_budget.state(),
                    spend=active_budget.get_local_spend_data_bcm(),
                    available=active_budget.get_local_available_data_bcm(),
                    canEditStartDate=active_budget.can_edit_start_date(),
                    canEditEndDate=active_budget.can_edit_end_date(),
                    canEditAmount=active_budget.can_edit_amount(),
                    createdBy=active_budget.created_by,
                    createdDt=active_budget.created_dt,
                    licenseFee=active_budget.credit.license_fee,
                )
            ],
        )
        self.assertEqual(len(resp_json["data"]["deals"]), 1)
        self.assertEqual(resp_json["data"]["deals"][0]["dealId"], deal.deal_id)
        self.assertEqual(resp_json["data"]["deals"][0]["numOfAccounts"], 0)
        self.assertEqual(resp_json["data"]["deals"][0]["numOfCampaigns"], 1)
        self.assertEqual(resp_json["data"]["deals"][0]["numOfAdgroups"], 0)

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
                    {"id": "123", "name": "manager1@outbrain.com"},
                    {"id": "456", "name": "manager2@outbrain.com"},
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
                "budgetsDepleted": [
                    self.campaign_budget_repr(
                        id=inactive_budget.id,
                        creditId=inactive_budget.credit.id,
                        amount=inactive_budget.amount,
                        margin=inactive_budget.margin,
                        comment=inactive_budget.comment,
                        startDate=inactive_budget.start_date,
                        endDate=inactive_budget.end_date,
                        state=inactive_budget.state(),
                        spend=inactive_budget.get_local_spend_data_bcm(),
                        available=inactive_budget.get_local_available_data_bcm(),
                        canEditStartDate=inactive_budget.can_edit_start_date(),
                        canEditEndDate=inactive_budget.can_edit_end_date(),
                        canEditAmount=inactive_budget.can_edit_amount(),
                        createdBy=inactive_budget.created_by,
                        createdDt=inactive_budget.created_dt,
                        licenseFee=inactive_budget.credit.license_fee,
                    )
                ],
                "accountCredits": [
                    self.credit_item_repr(
                        id=credit.pk,
                        totalAmount=credit.effective_amount(),
                        allocatedAmount=credit.get_allocated_amount(),
                        availableAmount=credit.get_available_amount(),
                        createdOn=credit.get_creation_date(),
                        startDate=credit.start_date,
                        endDate=credit.end_date,
                        comment=credit.comment,
                        status=credit.status,
                        currency=credit.currency,
                        isAvailable=credit.is_available(),
                        isAgency=credit.is_agency(),
                        licenseFee=credit.license_fee,
                    )
                ],
            },
        )

    @mock.patch("automation.autopilot.recalculate_budgets_campaign")
    @mock.patch("utils.email_helper.send_campaign_created_email")
    def test_post(self, mock_send, mock_autopilot):
        agency = magic_mixer.blend(core.models.Agency)
        account = magic_mixer.blend(core.models.Account, agency=agency, users=[self.user])
        credit = magic_mixer.blend(
            dash.models.CreditLineItem,
            account=account,
            start_date=datetime.date.today() - datetime.timedelta(30),
            end_date=datetime.date.today() + datetime.timedelta(30),
            amount=200000,
            currency=dash.constants.Currency.USD,
            status=dash.constants.CreditLineItemStatus.SIGNED,
        )

        source = magic_mixer.blend(core.models.Source, released=True, deprecated=False)
        deal = magic_mixer.blend(core.features.deals.DirectDeal, agency=agency, source=source)

        campaign_goal_time_on_site = self.campaign_goal_repr(
            type=dash.constants.CampaignGoalKPI.TIME_ON_SITE, primary=True
        )
        campaign_goal_new_unique_visitors = self.campaign_goal_repr(
            type=dash.constants.CampaignGoalKPI.NEW_UNIQUE_VISITORS, primary=False
        )

        campaign_budget = self.campaign_budget_repr(
            creditId=credit.id,
            amount="1000",
            margin="0.2500",
            comment="POST Campaign Budget",
            startDate=datetime.date.today(),
            endDate=datetime.date.today() + datetime.timedelta(5),
        )

        new_campaign = self.campaign_repr(
            account_id=account.id,
            campaign_manager=self.user.id,
            goals=[campaign_goal_time_on_site, campaign_goal_new_unique_visitors],
            budgets=[campaign_budget],
            deals=[{"id": str(deal.id), "dealId": deal.deal_id, "source": deal.source.bidder_slug}],
        )

        r = self.client.post(reverse("restapi.campaign.internal:campaigns_list"), data=new_campaign, format="json")
        resp_json = self.assertResponseValid(r, data_type=dict, status_code=201)

        self.assertEqual(resp_json["data"]["name"], new_campaign["name"])
        self.assertEqual(resp_json["data"]["accountId"], str(account.id))
        self.assertEqual(resp_json["data"]["type"], new_campaign["type"])
        self.assertEqual(resp_json["data"]["language"], new_campaign["language"])
        self.assertEqual(resp_json["data"]["iabCategory"], new_campaign["iabCategory"])
        self.assertEqual(resp_json["data"]["campaignManager"], str(new_campaign["campaignManager"]))
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
        self.assertEqual(len(resp_json["data"]["budgets"]), 1)
        self.assertIsNotNone(resp_json["data"]["budgets"][0]["id"])
        self.assertEqual(resp_json["data"]["budgets"][0]["creditId"], campaign_budget["creditId"])
        self.assertEqual(resp_json["data"]["budgets"][0]["amount"], campaign_budget["amount"])
        self.assertEqual(resp_json["data"]["budgets"][0]["comment"], campaign_budget["comment"])
        self.assertEqual(len(resp_json["data"]["deals"]), 1)
        self.assertEqual(resp_json["data"]["deals"][0]["dealId"], deal.deal_id)
        self.assertEqual(resp_json["data"]["deals"][0]["numOfAccounts"], 0)
        self.assertEqual(resp_json["data"]["deals"][0]["numOfCampaigns"], 1)
        self.assertEqual(resp_json["data"]["deals"][0]["numOfAdgroups"], 0)

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

        credit = magic_mixer.blend(
            dash.models.CreditLineItem,
            account=account,
            start_date=datetime.date.today() - datetime.timedelta(30),
            end_date=datetime.date.today() + datetime.timedelta(30),
            amount=200000,
            currency=dash.constants.Currency.USD,
            status=dash.constants.CreditLineItemStatus.SIGNED,
        )

        active_budget = magic_mixer.blend(
            dash.models.BudgetLineItem,
            campaign=campaign,
            credit=credit,
            start_date=datetime.date.today() - datetime.timedelta(1),
            end_date=datetime.date.today() + datetime.timedelta(5),
            created_by=self.user,
            amount=10000,
            margin=decimal.Decimal("0.2500"),
            comment="PUT Campaign Budget",
        )

        source = magic_mixer.blend(core.models.Source, released=True, deprecated=False)
        deal_to_be_removed = magic_mixer.blend(core.features.deals.DirectDeal, agency=agency, source=source)
        magic_mixer.blend(core.features.deals.DirectDealConnection, deal=deal_to_be_removed, campaign=campaign)

        deal_to_be_added = magic_mixer.blend(core.features.deals.DirectDeal, agency=agency, source=source)

        r = self.client.get(reverse("restapi.campaign.internal:campaigns_details", kwargs={"campaign_id": campaign.id}))
        resp_json = self.assertResponseValid(r)

        self.assertEqual(len(resp_json["data"]["goals"]), 1)
        self.assertEqual(len(resp_json["data"]["budgets"]), 1)
        self.assertEqual(len(resp_json["data"]["deals"]), 1)

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

        updated_amount = active_budget.amount + 100
        put_data["budgets"][0]["amount"] = str(updated_amount)

        put_data["deals"] = [
            {
                "id": str(deal_to_be_added.id),
                "dealId": deal_to_be_added.deal_id,
                "source": deal_to_be_added.source.bidder_slug,
            }
        ]

        r = self.client.put(
            reverse("restapi.campaign.internal:campaigns_details", kwargs={"campaign_id": campaign.id}),
            data=put_data,
            format="json",
        )
        resp_json = self.assertResponseValid(r)

        self.assertEqual(resp_json["data"]["campaignManager"], str(self.user.id))
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

        self.assertEqual(resp_json["data"]["budgets"][0]["amount"], str(updated_amount))

        self.assertEqual(len(resp_json["data"]["deals"]), 1)
        self.assertEqual(resp_json["data"]["deals"][0]["dealId"], deal_to_be_added.deal_id)
        self.assertEqual(resp_json["data"]["deals"][0]["numOfAccounts"], 0)
        self.assertEqual(resp_json["data"]["deals"][0]["numOfCampaigns"], 1)
        self.assertEqual(resp_json["data"]["deals"][0]["numOfAdgroups"], 0)
