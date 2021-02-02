import datetime
import decimal

import mock
from django.urls import reverse

import core.models
import dash.constants
import dash.features.clonecampaign.exceptions
import dash.features.clonecampaign.service
import dash.models
import dash.views.helpers
import restapi.serializers.targeting
from restapi.common.views_base_test_case import RESTAPITestCase
from utils import test_helper
from utils.magic_mixer import magic_mixer
from zemauth.features.entity_permission import Permission


class CampaignViewSetTest(RESTAPITestCase):
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
        target_environments=[dash.constants.AdTargetEnvironment.APP],
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
                "environments": restapi.serializers.targeting.EnvironmentsSerializer(target_environments).data,
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
        accountId=None,
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
        serviceFee=None,
        licenseFee=None,
    ):
        representation = {
            "accountId": str(accountId) if accountId is not None else None,
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
            "serviceFee": serviceFee,
            "licenseFee": licenseFee,
        }

        return cls.normalize(representation)

    @classmethod
    def credit_item_repr(
        cls,
        id=None,
        createdOn=None,
        createdBy=None,
        status=None,
        agencyId=None,
        agencyName=None,
        accountId=None,
        accountName=None,
        startDate=None,
        endDate=None,
        serviceFee=None,
        licenseFee=None,
        amount=None,
        total=None,
        allocated=None,
        available=None,
        currency=dash.constants.Currency.USD,
        contractId=None,
        contractNumber=None,
        comment=None,
        salesforceUrl=None,
        isAvailable=None,
    ):
        representation = {
            "id": str(id) if id is not None else None,
            "createdOn": createdOn,
            "createdBy": createdBy,
            "status": dash.constants.CreditLineItemStatus.get_name(status),
            "agencyId": str(agencyId) if agencyId is not None else None,
            "agencyName": agencyName,
            "accountId": str(accountId) if accountId is not None else None,
            "accountName": accountName,
            "startDate": startDate,
            "endDate": endDate,
            "serviceFee": str(serviceFee),
            "licenseFee": str(licenseFee),
            "amount": amount,
            "total": str(total),
            "allocated": str(allocated),
            "available": str(available),
            "currency": dash.constants.Currency.get_name(currency),
            "contractId": contractId,
            "contractNumber": contractNumber,
            "comment": comment,
            "salesforceUrl": salesforceUrl,
            "isAvailable": isAvailable,
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
        agency = magic_mixer.blend(core.models.Agency)
        account = self.mix_account(
            self.user,
            permissions=[
                Permission.READ,
                Permission.WRITE,
                Permission.AGENCY_SPEND_MARGIN,
                Permission.MEDIA_COST_DATA_COST_LICENCE_FEE,
                Permission.BASE_COSTS_SERVICE_FEE,
            ],
            agency=agency,
        )

        mock_get_extra_data.return_value = {
            "archived": False,
            "language": dash.constants.Language.ENGLISH,
            "can_restore": True,
            "agency_id": 12345,
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
                "base_media_spend": decimal.Decimal("0.0000"),
                "base_data_spend": decimal.Decimal("0.0000"),
                "media_spend": decimal.Decimal("0.0000"),
                "data_spend": decimal.Decimal("0.0000"),
                "service_fee": decimal.Decimal("0.0000"),
                "license_fee": decimal.Decimal("0.0000"),
                "margin": decimal.Decimal("0.0000"),
            },
            "budgets_depleted": [],
            "credits": [],
        }

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
                "canRestore": True,
                "agencyId": "12345",
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
                    "baseMediaSpend": "0.0000",
                    "baseDataSpend": "0.0000",
                    "mediaSpend": "0.0000",
                    "dataSpend": "0.0000",
                    "serviceFee": "0.0000",
                    "licenseFee": "0.0000",
                    "margin": "0.0000",
                },
                "budgetsDepleted": [],
                "credits": [],
                "agencyUsesRealtimeAutopilot": False,
            },
        )

    def test_get_defaults_invalid_params(self):
        r = self.client.get(reverse("restapi.campaign.internal:campaigns_defaults"), {"accountId": "NON-NUMERIC"})
        resp_json = self.assertResponseError(r, "ValidationError")
        self.assertEqual({"accountId": ["Invalid format"]}, resp_json["details"])

        r = self.client.get(reverse("restapi.campaign.internal:campaigns_defaults"))
        resp_json = self.assertResponseError(r, "ValidationError")
        self.assertEqual({"accountId": ["This field is required."]}, resp_json["details"])

        r = self.client.get(
            reverse("restapi.campaign.internal:campaigns_defaults"),
            {"accountId": "NON-NUMERIC", "offset": "NON-NUMERIC", "limit": "NON-NUMERIC"},
        )
        resp_json = self.assertResponseError(r, "ValidationError")
        self.assertEqual(
            {"limit": ["Invalid format"], "offset": ["Invalid format"], "accountId": ["Invalid format"]},
            resp_json["details"],
        )

    @mock.patch("restapi.campaign.internal.helpers.get_extra_data")
    def test_get(self, mock_get_extra_data):
        agency = magic_mixer.blend(core.models.Agency)
        account = self.mix_account(
            self.user,
            permissions=[
                Permission.READ,
                Permission.WRITE,
                Permission.AGENCY_SPEND_MARGIN,
                Permission.MEDIA_COST_DATA_COST_LICENCE_FEE,
                Permission.BASE_COSTS_SERVICE_FEE,
            ],
            agency=agency,
        )
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
            agency=None,
            account=account,
            start_date=datetime.date.today() - datetime.timedelta(30),
            end_date=datetime.date.today() + datetime.timedelta(30),
            amount=200000,
            currency=dash.constants.Currency.USD,
            status=dash.constants.CreditLineItemStatus.SIGNED,
            service_fee=decimal.Decimal("0.1000"),
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
        deal = magic_mixer.blend(core.features.deals.DirectDeal, account=account, source=source)
        magic_mixer.blend(core.features.deals.DirectDealConnection, deal=deal, campaign=campaign)

        mock_get_extra_data.return_value = {
            "archived": False,
            "language": dash.constants.Language.ENGLISH,
            "can_restore": True,
            "agency_id": 12345,
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
                "base_media_spend": decimal.Decimal("220.0000"),
                "base_data_spend": decimal.Decimal("100.0000"),
                "media_spend": decimal.Decimal("220.0000"),
                "data_spend": decimal.Decimal("100.0000"),
                "service_fee": decimal.Decimal("5.0000"),
                "license_fee": decimal.Decimal("5.0000"),
                "margin": decimal.Decimal("2.0000"),
            },
            "budgets_depleted": [inactive_budget],
            "credits": [credit],
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
                    accountId=active_budget.campaign.account_id,
                    id=active_budget.id,
                    creditId=active_budget.credit.id,
                    amount=active_budget.amount,
                    margin=dash.views.helpers.format_decimal_to_percent(active_budget.margin),
                    comment=active_budget.comment,
                    startDate=active_budget.start_date,
                    endDate=active_budget.end_date,
                    state=active_budget.state(),
                    spend=active_budget.get_local_etfm_spend_data(),
                    available=active_budget.get_local_etfm_available_data(),
                    canEditStartDate=active_budget.can_edit_start_date(),
                    canEditEndDate=active_budget.can_edit_end_date(),
                    canEditAmount=active_budget.can_edit_amount(),
                    createdBy=active_budget.created_by,
                    createdDt=active_budget.created_dt,
                    serviceFee=dash.views.helpers.format_decimal_to_percent(active_budget.credit.service_fee),
                    licenseFee=dash.views.helpers.format_decimal_to_percent(active_budget.credit.license_fee),
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
                "canRestore": True,
                "agencyId": "12345",
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
                    "baseMediaSpend": "220.0000",
                    "baseDataSpend": "100.0000",
                    "mediaSpend": "220.0000",
                    "dataSpend": "100.0000",
                    "serviceFee": "5.0000",
                    "licenseFee": "5.0000",
                    "margin": "2.0000",
                },
                "budgetsDepleted": [
                    self.campaign_budget_repr(
                        accountId=inactive_budget.campaign.account_id,
                        id=inactive_budget.id,
                        creditId=inactive_budget.credit.id,
                        amount=inactive_budget.amount,
                        margin=dash.views.helpers.format_decimal_to_percent(inactive_budget.margin),
                        comment=inactive_budget.comment,
                        startDate=inactive_budget.start_date,
                        endDate=inactive_budget.end_date,
                        state=inactive_budget.state(),
                        spend=inactive_budget.get_local_etfm_spend_data(),
                        available=inactive_budget.get_local_etfm_available_data(),
                        canEditStartDate=inactive_budget.can_edit_start_date(),
                        canEditEndDate=inactive_budget.can_edit_end_date(),
                        canEditAmount=inactive_budget.can_edit_amount(),
                        createdBy=inactive_budget.created_by,
                        createdDt=inactive_budget.created_dt,
                        serviceFee=dash.views.helpers.format_decimal_to_percent(inactive_budget.credit.service_fee),
                        licenseFee=dash.views.helpers.format_decimal_to_percent(inactive_budget.credit.license_fee),
                    )
                ],
                "credits": [
                    self.credit_item_repr(
                        id=credit.pk,
                        createdOn=credit.get_creation_date(),
                        createdBy=credit.created_by,
                        status=credit.status,
                        agencyId=credit.agency_id,
                        agencyName=credit.agency.name if credit.agency is not None else None,
                        accountId=credit.account_id,
                        accountName=credit.account.settings.name if credit.account is not None else None,
                        startDate=credit.start_date,
                        endDate=credit.end_date,
                        serviceFee=dash.views.helpers.format_decimal_to_percent(credit.service_fee),
                        licenseFee=dash.views.helpers.format_decimal_to_percent(credit.license_fee),
                        amount=credit.amount,
                        total=credit.effective_amount(),
                        allocated=credit.get_allocated_amount(),
                        available=credit.get_available_amount(),
                        currency=credit.currency,
                        contractId=credit.contract_id,
                        contractNumber=credit.contract_number,
                        comment=credit.comment,
                        salesforceUrl=credit.get_salesforce_url(),
                        isAvailable=credit.is_available(),
                    )
                ],
                "agencyUsesRealtimeAutopilot": False,
            },
        )

    def test_get_hide_agency_deal_id_for_account_user(self):
        agency = magic_mixer.blend(core.models.Agency)
        account = self.mix_account(
            self.user,
            permissions=[
                Permission.READ,
                Permission.WRITE,
                Permission.AGENCY_SPEND_MARGIN,
                Permission.MEDIA_COST_DATA_COST_LICENCE_FEE,
                Permission.BASE_COSTS_SERVICE_FEE,
            ],
            agency=agency,
        )
        campaign = magic_mixer.blend(
            core.models.Campaign, account=account, name="Test campaign", type=dash.constants.CampaignType.CONTENT
        )

        source = magic_mixer.blend(core.models.Source, released=True, deprecated=False)
        deal = magic_mixer.blend(core.features.deals.DirectDeal, agency=agency, source=source)
        magic_mixer.blend(core.features.deals.DirectDealConnection, deal=deal, campaign=campaign)

        r = self.client.get(reverse("restapi.campaign.internal:campaigns_details", kwargs={"campaign_id": campaign.id}))
        resp_json = self.assertResponseValid(r)

        self.assertEqual(len(resp_json["data"]["deals"]), 1)
        self.assertFalse("dealId" in resp_json["data"]["deals"][0])

    def test_get_readonly_no_deals(self):
        agency = magic_mixer.blend(core.models.Agency)
        account = self.mix_account(
            self.user,
            permissions=[
                Permission.READ,
                Permission.AGENCY_SPEND_MARGIN,
                Permission.MEDIA_COST_DATA_COST_LICENCE_FEE,
                Permission.BASE_COSTS_SERVICE_FEE,
            ],
            agency=agency,
        )
        campaign = magic_mixer.blend(
            core.models.Campaign, account=account, name="Test campaign", type=dash.constants.CampaignType.CONTENT
        )
        source = magic_mixer.blend(core.models.Source, released=True, deprecated=False)
        deal = magic_mixer.blend(core.features.deals.DirectDeal, agency=agency, source=source)
        magic_mixer.blend(core.features.deals.DirectDealConnection, deal=deal, campaign=campaign)

        r = self.client.get(reverse("restapi.campaign.internal:campaigns_details", kwargs={"campaign_id": campaign.id}))
        resp_json = self.assertResponseValid(r)
        self.assertFalse("deals" in resp_json["data"])

    @mock.patch("restapi.campaign.internal.helpers.get_extra_data")
    def test_get_limited(self, mock_get_extra_data):
        agency = magic_mixer.blend(core.models.Agency)
        account = self.mix_account(self.user, permissions=[Permission.READ], agency=agency)
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

        credit = magic_mixer.blend(
            dash.models.CreditLineItem,
            agency=None,
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

        mock_get_extra_data.return_value = {
            "archived": False,
            "language": dash.constants.Language.ENGLISH,
            "can_restore": True,
            "agency_id": 12345,
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
            },
            "budgets_depleted": [inactive_budget],
            "credits": [credit],
        }

        r = self.client.get(reverse("restapi.campaign.internal:campaigns_details", kwargs={"campaign_id": campaign.id}))
        resp_json = self.assertResponseValid(r)

        campaign_budget_repr = self.campaign_budget_repr(
            accountId=active_budget.campaign.account_id,
            id=active_budget.id,
            creditId=active_budget.credit.id,
            amount=active_budget.amount,
            comment=active_budget.comment,
            startDate=active_budget.start_date,
            endDate=active_budget.end_date,
            state=active_budget.state(),
            spend=active_budget.get_local_etfm_spend_data(),
            available=active_budget.get_local_etfm_available_data(),
            canEditStartDate=active_budget.can_edit_start_date(),
            canEditEndDate=active_budget.can_edit_end_date(),
            canEditAmount=active_budget.can_edit_amount(),
            createdBy=active_budget.created_by,
            createdDt=active_budget.created_dt,
        )
        del campaign_budget_repr["margin"]
        del campaign_budget_repr["licenseFee"]
        del campaign_budget_repr["serviceFee"]

        depleted_campaign_budget_repr = self.campaign_budget_repr(
            accountId=inactive_budget.campaign.account_id,
            id=inactive_budget.id,
            creditId=inactive_budget.credit.id,
            amount=inactive_budget.amount,
            comment=inactive_budget.comment,
            startDate=inactive_budget.start_date,
            endDate=inactive_budget.end_date,
            state=inactive_budget.state(),
            spend=inactive_budget.get_local_etfm_spend_data(),
            available=inactive_budget.get_local_etfm_available_data(),
            canEditStartDate=inactive_budget.can_edit_start_date(),
            canEditEndDate=inactive_budget.can_edit_end_date(),
            canEditAmount=inactive_budget.can_edit_amount(),
            createdBy=inactive_budget.created_by,
            createdDt=inactive_budget.created_dt,
        )
        del depleted_campaign_budget_repr["margin"]
        del depleted_campaign_budget_repr["licenseFee"]
        del depleted_campaign_budget_repr["serviceFee"]

        credit_item_repr = self.credit_item_repr(
            id=credit.pk,
            createdOn=credit.get_creation_date(),
            createdBy=credit.created_by,
            status=credit.status,
            agencyId=credit.agency_id,
            agencyName=credit.agency.name if credit.agency is not None else None,
            accountId=credit.account_id,
            accountName=credit.account.settings.name if credit.account is not None else None,
            startDate=credit.start_date,
            endDate=credit.end_date,
            licenseFee=dash.views.helpers.format_decimal_to_percent(credit.service_fee),
            serviceFee=dash.views.helpers.format_decimal_to_percent(credit.license_fee),
            amount=credit.amount,
            total=credit.effective_amount(),
            allocated=credit.get_allocated_amount(),
            available=credit.get_available_amount(),
            currency=credit.currency,
            contractId=credit.contract_id,
            contractNumber=credit.contract_number,
            comment=credit.comment,
            salesforceUrl=credit.get_salesforce_url(),
            isAvailable=credit.is_available(),
        )
        del credit_item_repr["licenseFee"]
        del credit_item_repr["serviceFee"]

        self.assertEqual(resp_json["data"]["budgets"], [campaign_budget_repr])
        self.assertEqual(
            resp_json["extra"],
            {
                "archived": False,
                "language": dash.constants.Language.get_name(dash.constants.Language.ENGLISH),
                "canRestore": True,
                "agencyId": "12345",
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
                },
                "budgetsDepleted": [depleted_campaign_budget_repr],
                "credits": [credit_item_repr],
                "agencyUsesRealtimeAutopilot": False,
            },
        )

    def test_get_internal_deals_no_permission(self):
        account = self.mix_account(self.user, permissions=[Permission.READ, Permission.WRITE], name="Generic account")
        campaign = magic_mixer.blend(core.models.Campaign, account=account)
        source = magic_mixer.blend(core.models.Source, released=True, deprecated=False)
        deal = magic_mixer.blend(core.features.deals.DirectDeal, account=account, source=source, is_internal=True)
        magic_mixer.blend(core.features.deals.DirectDealConnection, deal=deal, campaign=campaign)

        r = self.client.get(reverse("restapi.campaign.internal:campaigns_details", kwargs={"campaign_id": campaign.id}))
        resp_json = self.assertResponseValid(r)
        self.assertEqual(len(resp_json["data"]["deals"]), 0)

    def test_get_internal_deals_permission(self):
        account = self.mix_account(self.user, permissions=[Permission.READ, Permission.WRITE], name="Generic account")
        campaign = magic_mixer.blend(core.models.Campaign, account=account)
        source = magic_mixer.blend(core.models.Source, released=True, deprecated=False)
        deal = magic_mixer.blend(core.features.deals.DirectDeal, account=account, source=source, is_internal=True)
        magic_mixer.blend(core.features.deals.DirectDealConnection, deal=deal, campaign=campaign)

        test_helper.add_permissions(self.user, ["can_see_internal_deals"])
        r = self.client.get(reverse("restapi.campaign.internal:campaigns_details", kwargs={"campaign_id": campaign.id}))
        resp_json = self.assertResponseValid(r)
        self.assertEqual(len(resp_json["data"]["deals"]), 1)

    @mock.patch("automation.autopilot.recalculate_ad_group_budgets")
    @mock.patch("utils.email_helper.send_campaign_created_email")
    def test_post(self, mock_send, mock_autopilot):
        agency = self.mix_agency(
            self.user,
            permissions=[
                Permission.READ,
                Permission.WRITE,
                Permission.BUDGET,
                Permission.AGENCY_SPEND_MARGIN,
                Permission.MEDIA_COST_DATA_COST_LICENCE_FEE,
                Permission.BASE_COSTS_SERVICE_FEE,
            ],
        )
        account = magic_mixer.blend(core.models.Account, agency=agency)
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
            accountId="123",
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
            deals=[
                {
                    "id": str(deal.id),
                    "dealId": deal.deal_id,
                    "source": deal.source.bidder_slug,
                    "name": deal.name,
                    "agencyId": str(agency.id),
                },
                {
                    "id": None,
                    "dealId": "NEW_DEAL",
                    "source": source.bidder_slug,
                    "name": "NEW DEAL NAME",
                    "accountId": str(account.id),
                },
            ],
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
        self.assertEqual(len(resp_json["data"]["deals"]), 2)
        self.assertEqual(resp_json["data"]["deals"][0]["dealId"], deal.deal_id)
        self.assertEqual(resp_json["data"]["deals"][0]["numOfAccounts"], 0)
        self.assertEqual(resp_json["data"]["deals"][0]["numOfCampaigns"], 1)
        self.assertEqual(resp_json["data"]["deals"][0]["numOfAdgroups"], 0)
        self.assertEqual(resp_json["data"]["deals"][0]["agencyId"], str(agency.id))
        self.assertEqual(resp_json["data"]["deals"][0]["accountId"], None)

        self.assertEqual(resp_json["data"]["deals"][1]["dealId"], "NEW_DEAL")
        self.assertEqual(resp_json["data"]["deals"][1]["numOfAccounts"], 0)
        self.assertEqual(resp_json["data"]["deals"][1]["numOfCampaigns"], 1)
        self.assertEqual(resp_json["data"]["deals"][1]["numOfAdgroups"], 0)
        self.assertEqual(resp_json["data"]["deals"][1]["agencyId"], None)
        self.assertEqual(resp_json["data"]["deals"][1]["accountId"], str(account.id))

    def test_post_campaign_manager_error(self):
        agency = magic_mixer.blend(core.models.Agency)
        account = self.mix_agency(self.user, permissions=[Permission.READ, Permission.WRITE], agency=agency)

        new_campaign = self.campaign_repr(account_id=account.id, campaign_manager=904324)

        r = self.client.post(reverse("restapi.campaign.internal:campaigns_list"), data=new_campaign, format="json")
        r = self.assertResponseError(r, "ValidationError")

        self.assertIn("Invalid campaign manager.", r["details"]["campaignManager"][0])

    @mock.patch("automation.autopilot.recalculate_ad_group_budgets")
    @mock.patch("utils.email_helper.send_campaign_created_email")
    def test_post_goals_error(self, mock_send, mock_autopilot):
        agency = magic_mixer.blend(core.models.Agency)
        account = self.mix_account(self.user, permissions=[Permission.READ, Permission.WRITE], agency=agency)

        new_campaign = self.campaign_repr(account_id=account.id, campaign_manager=self.user.id, goals=[])

        r = self.client.post(reverse("restapi.campaign.internal:campaigns_list"), data=new_campaign, format="json")
        r = self.assertResponseError(r, "ValidationError")

        self.assertIn("At least one goal must be defined.", r["details"]["goalsMissing"][0])

    @mock.patch("automation.autopilot_legacy.recalculate_budgets_campaign")
    @mock.patch("utils.email_helper.send_campaign_created_email")
    def test_put(self, mock_send, mock_autopilot):
        agency = magic_mixer.blend(core.models.Agency)
        account = self.mix_account(
            self.user,
            permissions=[
                Permission.READ,
                Permission.WRITE,
                Permission.BUDGET,
                Permission.AGENCY_SPEND_MARGIN,
                Permission.MEDIA_COST_DATA_COST_LICENCE_FEE,
                Permission.BASE_COSTS_SERVICE_FEE,
            ],
            agency=agency,
        )
        campaign = magic_mixer.blend(
            core.models.Campaign, account=account, name="Test campaign", type=dash.constants.CampaignType.CONTENT
        )
        campaign.settings.update_unsafe(
            None,
            name=campaign.name,
            language=dash.constants.Language.ENGLISH,
            autopilot=True,
            iab_category=dash.constants.IABCategory.IAB4_6,
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
        deal_to_be_removed = magic_mixer.blend(core.features.deals.DirectDeal, account=account, source=source)
        magic_mixer.blend(core.features.deals.DirectDealConnection, deal=deal_to_be_removed, campaign=campaign)

        deal_to_be_added = magic_mixer.blend(core.features.deals.DirectDeal, account=account, source=source)

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
                "name": deal_to_be_added.name,
                "agencyId": agency.id,
            },
            {
                "id": None,
                "dealId": "NEW_DEAL",
                "source": source.bidder_slug,
                "name": "NEW DEAL NAME",
                "accountId": account.id,
            },
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

        self.assertEqual(len(resp_json["data"]["deals"]), 2)
        self.assertEqual(resp_json["data"]["deals"][0]["dealId"], deal_to_be_added.deal_id)
        self.assertEqual(resp_json["data"]["deals"][0]["numOfAccounts"], 0)
        self.assertEqual(resp_json["data"]["deals"][0]["numOfCampaigns"], 1)
        self.assertEqual(resp_json["data"]["deals"][0]["numOfAdgroups"], 0)
        self.assertEqual(resp_json["data"]["deals"][1]["agencyId"], None)
        self.assertEqual(resp_json["data"]["deals"][1]["accountId"], str(account.id))
        self.assertEqual(resp_json["data"]["deals"][1]["dealId"], "NEW_DEAL")
        self.assertEqual(resp_json["data"]["deals"][1]["numOfAccounts"], 0)
        self.assertEqual(resp_json["data"]["deals"][1]["numOfCampaigns"], 1)
        self.assertEqual(resp_json["data"]["deals"][1]["numOfAdgroups"], 0)
        self.assertEqual(resp_json["data"]["deals"][1]["agencyId"], None)
        self.assertEqual(resp_json["data"]["deals"][1]["accountId"], str(account.id))

    def test_put_undefined_iab_category(self):
        agency = self.mix_agency(self.user, permissions=[Permission.READ, Permission.WRITE])
        account = magic_mixer.blend(core.models.Account, agency=agency)
        campaign = magic_mixer.blend(
            core.models.Campaign, account=account, name="Test campaign", type=dash.constants.CampaignType.CONTENT
        )

        put_data = {"iab_category": dash.constants.IABCategory.IAB24}
        response = self.client.put(
            reverse("restapi.campaign.internal:campaigns_details", kwargs={"campaign_id": campaign.id}),
            data=put_data,
            format="json",
        )
        resp_json = self.assertResponseError(response, error_code="ValidationError")
        self.assertEqual(resp_json["details"], {"iabCategory": ["Invalid IAB category."]})

    @mock.patch.object(dash.features.clonecampaign.service, "clone", autospec=True)
    def test_clone(self, mock_clone):
        agency = magic_mixer.blend(core.models.Agency)
        account = self.mix_account(self.user, permissions=[Permission.READ, Permission.WRITE], agency=agency)
        campaign = magic_mixer.blend(core.models.Campaign, account=account)
        cloned_campaign = magic_mixer.blend(core.models.Campaign)
        mock_clone.return_value = cloned_campaign

        data = self.normalize(
            {
                "destinationCampaignName": "New campaign clone",
                "cloneAdGroups": True,
                "cloneAds": True,
                "adGroupStateOverride": "ACTIVE",
                "adStateOverride": "ACTIVE",
            }
        )

        r = self.client.post(
            reverse("restapi.campaign.internal:campaigns_clone", kwargs={"campaign_id": campaign.id}),
            data=data,
            format="json",
        )
        r = self.assertResponseValid(r, data_type=dict, status_code=201)
        self.assertDictContainsSubset({"id": str(cloned_campaign.pk)}, r["data"])
        mock_clone.assert_called_with(
            mock.ANY,
            campaign,
            destination_campaign_name=data["destinationCampaignName"],
            clone_ad_groups=data["cloneAdGroups"],
            clone_ads=data["cloneAds"],
            ad_group_state_override=dash.constants.ContentAdSourceState.get_constant_value(
                data["adGroupStateOverride"]
            ),
            ad_state_override=dash.constants.ContentAdSourceState.get_constant_value(data["adStateOverride"]),
        )

    @mock.patch.object(dash.features.clonecampaign.service, "clone", autospec=True)
    def test_clone_with_empty_values(self, mock_clone):
        agency = magic_mixer.blend(core.models.Agency)
        account = self.mix_account(self.user, permissions=[Permission.READ, Permission.WRITE], agency=agency)
        campaign = magic_mixer.blend(core.models.Campaign, account=account)
        cloned_campaign = magic_mixer.blend(core.models.Campaign)
        mock_clone.return_value = cloned_campaign

        data = self.normalize(
            {
                "destinationCampaignName": "New campaign clone",
                "cloneAdGroups": True,
                "cloneAds": True,
                "adGroupStateOverride": None,
            }
        )

        r = self.client.post(
            reverse("restapi.campaign.internal:campaigns_clone", kwargs={"campaign_id": campaign.id}),
            data=data,
            format="json",
        )
        r = self.assertResponseValid(r, data_type=dict, status_code=201)
        self.assertDictContainsSubset({"id": str(cloned_campaign.pk)}, r["data"])
        mock_clone.assert_called_with(
            mock.ANY,
            campaign,
            destination_campaign_name=data["destinationCampaignName"],
            clone_ad_groups=data["cloneAdGroups"],
            clone_ads=data["cloneAds"],
            ad_group_state_override=dash.constants.ContentAdSourceState.get_constant_value(
                data["adGroupStateOverride"]
            ),
        )

    def test_clone_with_exception(self):
        agency = magic_mixer.blend(core.models.Agency)
        account = self.mix_account(self.user, permissions=[Permission.READ, Permission.WRITE], agency=agency)
        campaign = magic_mixer.blend(core.models.Campaign, account=account)

        data = self.normalize(
            {
                "destinationCampaignName": "New campaign clone",
                "cloneAdGroups": False,
                "cloneAds": True,
                "adGroupStateOverride": "ACTIVE",
                "adStateOverride": "ACTIVE",
            }
        )

        r = self.client.post(
            reverse("restapi.campaign.internal:campaigns_clone", kwargs={"campaign_id": campaign.id}),
            data=data,
            format="json",
        )
        self.assertResponseError(r, "ValidationError")

    @mock.patch("dash.features.alerts.get_campaign_alerts")
    def test_get_alerts(self, mock_get_campaign_alerts):
        mock_get_campaign_alerts.return_value = []

        account = self.mix_account(self.user, permissions=[Permission.READ])
        campaign = magic_mixer.blend(core.models.Campaign, account=account)

        r = self.client.get(
            reverse("restapi.campaign.internal:campaigns_alerts", kwargs={"campaign_id": campaign.id}),
            data={"breakdown": "placement", "startDate": "2020-04-01"},
        )
        resp_json = self.assertResponseValid(r, data_type=list)
        self.assertEqual(len(resp_json["data"]), 0)

        mock_get_campaign_alerts.assert_called_once_with(
            mock.ANY,
            campaign,
            breakdown="placement",
            start_date=datetime.datetime.strptime("2020-04-01", "%Y-%m-%d").date(),
        )

    def test_get_alerts_invalid_params(self):
        account = self.mix_account(self.user, permissions=[Permission.READ])
        campaign = magic_mixer.blend(core.models.Campaign, account=account)

        r = self.client.get(
            reverse("restapi.campaign.internal:campaigns_alerts", kwargs={"campaign_id": campaign.id}),
            data={"startDate": "INVALID_VALUE_START_DATE"},
        )
        resp_json = self.assertResponseError(r, "ValidationError")
        self.assertEqual(
            {"startDate": ["Date has wrong format. Use one of these formats instead: YYYY[-MM[-DD]]."]},
            resp_json["details"],
        )

    def test_get_alerts_no_access(self):
        campaign = magic_mixer.blend(core.models.Campaign)

        r = self.client.get(
            reverse("restapi.campaign.internal:campaigns_alerts", kwargs={"campaign_id": campaign.id}),
            data={"breakdown": "placement", "startDate": "2020-04-01"},
        )
        self.assertResponseError(r, "MissingDataError")

    def test_list_account_id(self):
        account_one = self.mix_account(self.user, permissions=[Permission.READ])
        account_two = self.mix_account(self.user, permissions=[Permission.READ])

        campaigns_one = magic_mixer.cycle(5).blend(core.models.Campaign, account=account_one)
        magic_mixer.cycle(5).blend(core.models.Campaign, account=account_two)

        r = self.client.get(reverse("restapi.campaign.internal:campaigns_list"), data={"account_id": account_one.id})
        resp_json = self.assertResponseValid(r, data_type=list)
        resp_json_ids = sorted([x.get("id") for x in resp_json["data"]])
        campaigns_one_ids = sorted([str(x.id) for x in campaigns_one])
        self.assertEqual(resp_json_ids, campaigns_one_ids)

    def test_list_agency_id(self):
        agency_one = self.mix_agency(self.user, permissions=[Permission.READ])
        agency_two = self.mix_agency(self.user, permissions=[Permission.READ])

        campaigns_one = magic_mixer.cycle(5).blend(core.models.Campaign, account__agency=agency_one)
        magic_mixer.cycle(5).blend(core.models.Campaign, account__agency=agency_two)

        r = self.client.get(reverse("restapi.campaign.internal:campaigns_list"), data={"agency_id": agency_one.id})
        resp_json = self.assertResponseValid(r, data_type=list)
        resp_json_ids = sorted([x.get("id") for x in resp_json["data"]])
        campaigns_one_ids = sorted([str(x.id) for x in campaigns_one])
        self.assertEqual(resp_json_ids, campaigns_one_ids)

    def test_accounts_list_no_access(self):
        account = magic_mixer.blend(core.models.Account)
        magic_mixer.cycle(5).blend(core.models.Campaign, account=account)

        r = self.client.get(reverse("restapi.campaign.internal:campaigns_list"), data={"account_id": account.id})
        self.assertResponseError(r, "MissingDataError")
