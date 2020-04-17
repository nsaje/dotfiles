import datetime
import decimal

import mock
from django.urls import reverse

import core.features.bcm
import core.models
import dash.constants
import utils.test_helper
from restapi.common.views_base_test import RESTAPITest
from utils.magic_mixer import magic_mixer


class CreditViewSetTest(RESTAPITest):
    def test_get(self):
        agency = magic_mixer.blend(core.models.Agency)
        account = magic_mixer.blend(core.models.Account, agency=agency, users=[self.user])
        credit = magic_mixer.blend(
            core.features.bcm.CreditLineItem,
            account=account,
            start_date=datetime.date.today(),
            end_date=datetime.date.today() + datetime.timedelta(30),
            amount=200000,
            currency=dash.constants.Currency.USD,
            status=dash.constants.CreditLineItemStatus.SIGNED,
            comment="Credit comment",
        )

        r = self.client.get(reverse("restapi.credit.internal:credits_details", kwargs={"credit_id": credit.id}))
        resp_json = self.assertResponseValid(r)

        self.assertEqual(resp_json["data"]["id"], str(credit.id))
        self.assertEqual(resp_json["data"]["createdOn"], self.normalize(credit.get_creation_date()))
        self.assertEqual(resp_json["data"]["status"], dash.constants.CreditLineItemStatus.get_name(credit.status))
        self.assertEqual(resp_json["data"]["agencyId"], None)
        self.assertEqual(resp_json["data"]["accountId"], str(account.id))
        self.assertEqual(resp_json["data"]["startDate"], self.normalize(credit.start_date))
        self.assertEqual(resp_json["data"]["endDate"], self.normalize(credit.end_date))
        self.assertEqual(resp_json["data"]["currency"], dash.constants.Currency.get_name(credit.currency))
        self.assertEqual(resp_json["data"]["comment"], credit.comment)
        self.assertEqual(resp_json["data"]["isAvailable"], credit.is_available())
        self.assertEqual(resp_json["data"]["numOfBudgets"], 0)

    def test_get_no_access(self):
        agency = magic_mixer.blend(core.models.Agency)
        account = magic_mixer.blend(core.models.Account, agency=agency)
        credit = magic_mixer.blend(
            core.features.bcm.CreditLineItem,
            account=account,
            start_date=datetime.date.today(),
            end_date=datetime.date.today() + datetime.timedelta(30),
            amount=200000,
            currency=dash.constants.Currency.USD,
            status=dash.constants.CreditLineItemStatus.SIGNED,
            comment="Credit comment",
        )

        r = self.client.get(reverse("restapi.credit.internal:credits_details", kwargs={"credit_id": credit.id}))
        self.assertResponseError(r, "MissingDataError")

    def test_get_no_permission(self):
        utils.test_helper.remove_permissions(self.user, ["account_credit_view"])
        agency = magic_mixer.blend(core.models.Agency)
        account = magic_mixer.blend(core.models.Account, agency=agency, users=[self.user])
        credit = magic_mixer.blend(
            core.features.bcm.CreditLineItem,
            account=account,
            start_date=datetime.date.today(),
            end_date=datetime.date.today() + datetime.timedelta(30),
            amount=200000,
            currency=dash.constants.Currency.USD,
            status=dash.constants.CreditLineItemStatus.SIGNED,
            comment="Credit comment",
        )

        r = self.client.get(reverse("restapi.credit.internal:credits_details", kwargs={"credit_id": credit.id}))
        self.assertEqual(r.status_code, 403)
        resp_json = self.assertResponseError(r, "PermissionDenied")
        self.assertEqual(
            resp_json,
            {"errorCode": "PermissionDenied", "details": "You do not have permission to perform this action."},
        )

    @mock.patch("core.features.bcm.bcm_slack.log_to_slack")
    def test_list_pagination_with_agency(self, mock_log_to_slack):
        agency = magic_mixer.blend(core.models.Agency, users=[self.user])
        # active credits
        magic_mixer.cycle(20).blend(
            core.features.bcm.CreditLineItem,
            agency=agency,
            account=None,
            start_date=datetime.date.today(),
            end_date=datetime.date.today() + datetime.timedelta(30),
            amount=200000,
            currency=dash.constants.Currency.USD,
            status=dash.constants.CreditLineItemStatus.SIGNED,
        )
        # past credits
        magic_mixer.cycle(20).blend(
            core.features.bcm.CreditLineItem,
            agency=agency,
            account=None,
            start_date=datetime.date.today() - datetime.timedelta(30),
            end_date=datetime.date.today() - datetime.timedelta(10),
            amount=200000,
            currency=dash.constants.Currency.USD,
            status=dash.constants.CreditLineItemStatus.SIGNED,
        )

        r = self.client.get(
            reverse("restapi.credit.internal:credits_list"), {"agencyId": agency.id, "offset": 0, "limit": 40}
        )
        resp_json = self.assertResponseValid(r, data_type=list)
        self.assertEqual(resp_json["count"], 40)
        self.assertIsNone(resp_json["next"])

        r_paginated = self.client.get(
            reverse("restapi.credit.internal:credits_list"), {"agencyId": agency.id, "offset": 10, "limit": 10}
        )
        resp_json_paginated = self.assertResponseValid(r_paginated, data_type=list)
        self.assertEqual(resp_json_paginated["count"], 40)
        self.assertIsNotNone(resp_json_paginated["previous"])
        self.assertIsNotNone(resp_json_paginated["next"])

        resp_json_ids = sorted([int(item.get("id")) for item in resp_json["data"][10:20]])
        resp_json_paginated_ids = sorted([int(item.get("id")) for item in resp_json_paginated["data"]])
        self.assertEqual(resp_json_ids, resp_json_paginated_ids)

    def test_list_invalid_params(self):
        r = self.client.get(
            reverse("restapi.credit.internal:credits_list"),
            {
                "agencyId": "NON-NUMERICAL",
                "accountId": "NON-NUMERICAL",
                "offset": "NON-NUMERICAL",
                "limit": "NON-NUMERICAL",
            },
        )
        resp_json = self.assertResponseError(r, "ValidationError")
        self.assertEqual(
            {
                "agencyId": ["Invalid format"],
                "accountId": ["Invalid format"],
                "offset": ["Invalid format"],
                "limit": ["Invalid format"],
            },
            resp_json["details"],
        )

    @mock.patch("core.features.bcm.bcm_slack.log_to_slack")
    def test_list_pagination_with_account(self, mock_log_to_slack):
        agency = magic_mixer.blend(core.models.Agency, users=[self.user])
        account_one = magic_mixer.blend(core.models.Account, agency=agency, users=[self.user])
        account_two = magic_mixer.blend(core.models.Account, agency=agency, users=[self.user])
        # credits on agency level
        agency_credits = magic_mixer.cycle(10).blend(
            core.features.bcm.CreditLineItem,
            agency=agency,
            account=None,
            start_date=datetime.date.today(),
            end_date=datetime.date.today() + datetime.timedelta(30),
            amount=200000,
            currency=dash.constants.Currency.USD,
            status=dash.constants.CreditLineItemStatus.SIGNED,
        )
        # credits on account_one level
        account_one_credits = magic_mixer.cycle(10).blend(
            core.features.bcm.CreditLineItem,
            agency=None,
            account=account_one,
            start_date=datetime.date.today(),
            end_date=datetime.date.today() + datetime.timedelta(30),
            amount=200000,
            currency=dash.constants.Currency.USD,
            status=dash.constants.CreditLineItemStatus.SIGNED,
        )
        # credits on account_two level
        magic_mixer.cycle(10).blend(
            core.features.bcm.CreditLineItem,
            agency=None,
            account=account_two,
            start_date=datetime.date.today(),
            end_date=datetime.date.today() + datetime.timedelta(30),
            amount=200000,
            currency=dash.constants.Currency.USD,
            status=dash.constants.CreditLineItemStatus.SIGNED,
        )

        r = self.client.get(
            reverse("restapi.credit.internal:credits_list"), {"accountId": account_one.id, "offset": 0, "limit": 30}
        )
        resp_json = self.assertResponseValid(r, data_type=list)
        self.assertEqual(resp_json["count"], 20)
        self.assertIsNone(resp_json["previous"])
        self.assertIsNone(resp_json["next"])

        credit_ids = sorted([credit.id for credit in agency_credits + account_one_credits])
        resp_json_ids = sorted([int(item.get("id")) for item in resp_json["data"]])
        self.assertEqual(credit_ids, resp_json_ids)

    @mock.patch("core.features.bcm.bcm_slack.log_to_slack")
    def test_list_active_pagination(self, mock_log_to_slack):
        agency = magic_mixer.blend(core.models.Agency, users=[self.user])
        # active credits
        active_credits = magic_mixer.cycle(20).blend(
            core.features.bcm.CreditLineItem,
            agency=agency,
            account=None,
            start_date=datetime.date.today(),
            end_date=datetime.date.today() + datetime.timedelta(30),
            amount=200000,
            currency=dash.constants.Currency.USD,
            status=dash.constants.CreditLineItemStatus.SIGNED,
        )
        # past credits
        magic_mixer.cycle(20).blend(
            core.features.bcm.CreditLineItem,
            agency=agency,
            account=None,
            start_date=datetime.date.today() - datetime.timedelta(30),
            end_date=datetime.date.today() - datetime.timedelta(10),
            amount=200000,
            currency=dash.constants.Currency.USD,
            status=dash.constants.CreditLineItemStatus.SIGNED,
        )

        r = self.client.get(
            reverse("restapi.credit.internal:credits_list"),
            {"agencyId": agency.id, "offset": 0, "limit": 40, "active": True},
        )
        resp_json = self.assertResponseValid(r, data_type=list)
        self.assertEqual(resp_json["count"], 20)
        self.assertIsNone(resp_json["next"])

        active_credit_ids = sorted([credit.id for credit in active_credits])
        resp_json_ids = sorted([int(item.get("id")) for item in resp_json["data"]])
        self.assertEqual(active_credit_ids, resp_json_ids)

        r_paginated = self.client.get(
            reverse("restapi.credit.internal:credits_list"),
            {"agencyId": agency.id, "offset": 10, "limit": 10, "active": True},
        )
        resp_json_paginated = self.assertResponseValid(r_paginated, data_type=list)
        self.assertEqual(resp_json_paginated["count"], 20)
        self.assertIsNotNone(resp_json_paginated["previous"])
        self.assertIsNone(resp_json_paginated["next"])

        active_credit_paginated_ids = sorted([int(item.get("id")) for item in resp_json["data"][10:20]])
        resp_json_paginated_ids = sorted([int(item.get("id")) for item in resp_json_paginated["data"]])
        self.assertEqual(active_credit_paginated_ids, resp_json_paginated_ids)

    @mock.patch("core.features.bcm.bcm_slack.log_to_slack")
    def test_list_past_pagination(self, mock_log_to_slack):
        agency = magic_mixer.blend(core.models.Agency, users=[self.user])
        # active credits
        magic_mixer.cycle(20).blend(
            core.features.bcm.CreditLineItem,
            agency=agency,
            account=None,
            start_date=datetime.date.today(),
            end_date=datetime.date.today() + datetime.timedelta(30),
            amount=200000,
            currency=dash.constants.Currency.USD,
            status=dash.constants.CreditLineItemStatus.SIGNED,
        )
        # past credits
        past_credits = magic_mixer.cycle(20).blend(
            core.features.bcm.CreditLineItem,
            agency=agency,
            account=None,
            start_date=datetime.date.today() - datetime.timedelta(30),
            end_date=datetime.date.today() - datetime.timedelta(10),
            amount=200000,
            currency=dash.constants.Currency.USD,
            status=dash.constants.CreditLineItemStatus.SIGNED,
        )

        r = self.client.get(
            reverse("restapi.credit.internal:credits_list"),
            {"agencyId": agency.id, "offset": 0, "limit": 40, "active": False},
        )
        resp_json = self.assertResponseValid(r, data_type=list)
        self.assertEqual(resp_json["count"], 20)
        self.assertIsNone(resp_json["next"])

        past_credit_ids = sorted([credit.id for credit in past_credits])
        resp_json_ids = sorted([int(item.get("id")) for item in resp_json["data"]])
        self.assertEqual(past_credit_ids, resp_json_ids)

        r_paginated = self.client.get(
            reverse("restapi.credit.internal:credits_list"),
            {"agencyId": agency.id, "offset": 10, "limit": 10, "active": False},
        )
        resp_json_paginated = self.assertResponseValid(r_paginated, data_type=list)
        self.assertEqual(resp_json_paginated["count"], 20)
        self.assertIsNotNone(resp_json_paginated["previous"])
        self.assertIsNone(resp_json_paginated["next"])

        past_credit_paginated_ids = sorted([int(item.get("id")) for item in resp_json["data"][10:20]])
        resp_json_paginated_ids = sorted([int(item.get("id")) for item in resp_json_paginated["data"]])
        self.assertEqual(past_credit_paginated_ids, resp_json_paginated_ids)

    @mock.patch("core.features.bcm.bcm_slack.log_to_slack")
    def test_totals(self, mock_log_to_slack):
        agency = magic_mixer.blend(core.models.Agency, users=[self.user])
        # active credits EUR
        magic_mixer.cycle(10).blend(
            core.features.bcm.CreditLineItem,
            agency=agency,
            account=None,
            start_date=datetime.date.today(),
            end_date=datetime.date.today() + datetime.timedelta(30),
            amount=10,
            currency=dash.constants.Currency.EUR,
            status=dash.constants.CreditLineItemStatus.SIGNED,
        )
        # active credits USD
        magic_mixer.cycle(10).blend(
            core.features.bcm.CreditLineItem,
            agency=agency,
            account=None,
            start_date=datetime.date.today(),
            end_date=datetime.date.today() + datetime.timedelta(30),
            amount=10,
            currency=dash.constants.Currency.USD,
            status=dash.constants.CreditLineItemStatus.SIGNED,
        )
        # past credits USD
        magic_mixer.cycle(10).blend(
            core.features.bcm.CreditLineItem,
            agency=agency,
            account=None,
            start_date=datetime.date.today() - datetime.timedelta(30),
            end_date=datetime.date.today() - datetime.timedelta(10),
            amount=10,
            currency=dash.constants.Currency.USD,
            status=dash.constants.CreditLineItemStatus.SIGNED,
        )

        r = self.client.get(reverse("restapi.credit.internal:credits_totals"), {"agencyId": agency.id})
        resp_json = self.assertResponseValid(r, data_type=list)

        self.assertEqual(len(resp_json["data"]), 2)

        for item in resp_json["data"]:
            if item.get("currency") == dash.constants.Currency.get_name(dash.constants.Currency.EUR):
                self.assertEqual(item["total"], "100.0000")
                self.assertEqual(item["allocated"], "0.0000")
                self.assertEqual(item["past"], "0.0000")
                self.assertEqual(item["available"], "100.0000")
            elif item.get("currency") == dash.constants.Currency.get_name(dash.constants.Currency.USD):
                self.assertEqual(item["total"], "200.0000")
                self.assertEqual(item["allocated"], "0.0000")
                self.assertEqual(item["past"], "100.0000")
                self.assertEqual(item["available"], "100.0000")

    def test_totals_invalid_params(self):
        r = self.client.get(
            reverse("restapi.credit.internal:credits_totals"),
            {"agencyId": "NON-NUMERICAL", "accountId": "NON-NUMERICAL"},
        )
        resp_json = self.assertResponseError(r, "ValidationError")
        self.assertEqual({"agencyId": ["Invalid format"], "accountId": ["Invalid format"]}, resp_json["details"])

    @mock.patch("core.features.bcm.bcm_slack.log_to_slack")
    def test_put(self, mock_log_to_slack):
        agency = magic_mixer.blend(core.models.Agency, users=[self.user])
        credit = magic_mixer.blend(
            core.features.bcm.CreditLineItem,
            agency=agency,
            account=None,
            start_date=datetime.date.today(),
            end_date=datetime.date.today() + datetime.timedelta(30),
            amount=200,
            currency=dash.constants.Currency.USD,
            status=dash.constants.CreditLineItemStatus.SIGNED,
            comment="Credit comment",
        )

        r = self.client.get(reverse("restapi.credit.internal:credits_details", kwargs={"credit_id": credit.id}))
        resp_json = self.assertResponseValid(r)

        self.assertEqual(
            resp_json["data"]["status"],
            dash.constants.CreditLineItemStatus.get_name(dash.constants.CreditLineItemStatus.SIGNED),
        )

        put_data = resp_json["data"].copy()
        put_data["status"] = dash.constants.CreditLineItemStatus.get_name(dash.constants.CreditLineItemStatus.CANCELED)

        r = self.client.put(
            reverse("restapi.credit.internal:credits_details", kwargs={"credit_id": credit.id}),
            data=put_data,
            format="json",
        )
        resp_json = self.assertResponseValid(r)

        self.assertEqual(
            resp_json["data"]["status"],
            dash.constants.CreditLineItemStatus.get_name(dash.constants.CreditLineItemStatus.CANCELED),
        )

    @mock.patch("core.features.bcm.bcm_slack.log_to_slack")
    def test_put_account(self, mock_log_to_slack):
        agency = magic_mixer.blend(core.models.Agency, users=[self.user])
        account = magic_mixer.blend(core.models.Account, agency=agency, users=[self.user])
        credit = magic_mixer.blend(
            core.features.bcm.CreditLineItem,
            agency=agency,
            account=None,
            start_date=datetime.date.today(),
            end_date=datetime.date.today() + datetime.timedelta(30),
            amount=200,
            currency=dash.constants.Currency.USD,
            status=dash.constants.CreditLineItemStatus.SIGNED,
            comment="Credit comment",
        )

        r = self.client.get(reverse("restapi.credit.internal:credits_details", kwargs={"credit_id": credit.id}))
        resp_json = self.assertResponseValid(r)

        self.assertEqual(resp_json["data"]["agencyId"], str(agency.id))
        self.assertEqual(resp_json["data"]["accountId"], None)

        put_data = resp_json["data"].copy()
        put_data["agencyId"] = None
        put_data["accountId"] = str(account.id)

        r = self.client.put(
            reverse("restapi.credit.internal:credits_details", kwargs={"credit_id": credit.id}),
            data=put_data,
            format="json",
        )
        resp_json = self.assertResponseValid(r)

        self.assertEqual(resp_json["data"]["agencyId"], None)
        self.assertEqual(resp_json["data"]["accountId"], str(account.id))

    @mock.patch("core.features.bcm.bcm_slack.log_to_slack")
    def test_put_error(self, mock_log_to_slack):
        agency = magic_mixer.blend(core.models.Agency, users=[self.user])
        account = magic_mixer.blend(core.models.Account, agency=agency, users=[self.user])
        credit = magic_mixer.blend(
            core.features.bcm.CreditLineItem,
            agency=None,
            account=account,
            start_date=datetime.date.today(),
            end_date=datetime.date.today() + datetime.timedelta(30),
            amount=200,
            currency=dash.constants.Currency.USD,
            status=dash.constants.CreditLineItemStatus.SIGNED,
            comment="Credit comment",
        )

        r = self.client.get(reverse("restapi.credit.internal:credits_details", kwargs={"credit_id": credit.id}))
        resp_json = self.assertResponseValid(r)

        self.assertEqual(resp_json["data"]["agencyId"], None)
        self.assertEqual(resp_json["data"]["accountId"], str(account.id))

        put_data = resp_json["data"].copy()
        put_data["accountId"] = None

        r = self.client.put(
            reverse("restapi.credit.internal:credits_details", kwargs={"credit_id": credit.id}),
            data=put_data,
            format="json",
        )
        resp_json = self.assertResponseError(r, "ValidationError")

        error_message = "One of either account or agency must be set."
        self.assertIn(error_message, resp_json["details"]["accountId"])
        self.assertIn(error_message, resp_json["details"]["agencyId"])

    @mock.patch("core.features.bcm.bcm_slack.log_to_slack")
    def test_put_account_error(self, mock_log_to_slack):
        agency = magic_mixer.blend(core.models.Agency, users=[self.user])
        account_one = magic_mixer.blend(core.models.Account, agency=agency, users=[self.user])
        account_two = magic_mixer.blend(core.models.Account, agency=agency, users=[self.user])
        campaign = magic_mixer.blend(
            core.models.Campaign, account=account_one, type=dash.constants.CampaignType.CONTENT
        )
        credit = magic_mixer.blend(
            core.features.bcm.CreditLineItem,
            agency=None,
            account=account_one,
            start_date=datetime.date.today(),
            end_date=datetime.date.today() + datetime.timedelta(30),
            amount=200,
            currency=dash.constants.Currency.USD,
            status=dash.constants.CreditLineItemStatus.SIGNED,
            comment="Credit comment",
        )
        magic_mixer.blend(
            core.features.bcm.BudgetLineItem,
            campaign=campaign,
            credit=credit,
            start_date=datetime.date.today() + datetime.timedelta(1),
            end_date=datetime.date.today() + datetime.timedelta(5),
            created_by=self.user,
            amount=10,
            margin=decimal.Decimal("0.2500"),
        )

        r = self.client.get(reverse("restapi.credit.internal:credits_details", kwargs={"credit_id": credit.id}))
        resp_json = self.assertResponseValid(r)

        self.assertEqual(resp_json["data"]["agencyId"], None)
        self.assertEqual(resp_json["data"]["accountId"], str(account_one.id))

        put_data = resp_json["data"].copy()
        put_data["accountId"] = str(account_two.id)

        r = self.client.put(
            reverse("restapi.credit.internal:credits_details", kwargs={"credit_id": credit.id}),
            data=put_data,
            format="json",
        )
        resp_json = self.assertResponseError(r, "ValidationError")

        error_message = "Credit line item is used outside of the scope of {account_name} account. To change the scope of the credit line item to {account_name} stop using it on other accounts (and their campaigns and ad groups) and try again.".format(
            account_name=account_two.name
        )
        self.assertIn(error_message, resp_json["details"]["accountId"])

    @mock.patch("core.features.bcm.bcm_slack.log_to_slack")
    def test_put_agency_error(self, mock_log_to_slack):
        agency_one = magic_mixer.blend(core.models.Agency, users=[self.user])
        agency_two = magic_mixer.blend(core.models.Agency, users=[self.user])
        account = magic_mixer.blend(core.models.Account, agency=agency_one, users=[self.user])
        campaign = magic_mixer.blend(core.models.Campaign, account=account, type=dash.constants.CampaignType.CONTENT)
        credit = magic_mixer.blend(
            core.features.bcm.CreditLineItem,
            agency=agency_one,
            account=None,
            start_date=datetime.date.today(),
            end_date=datetime.date.today() + datetime.timedelta(30),
            amount=200,
            currency=dash.constants.Currency.USD,
            status=dash.constants.CreditLineItemStatus.SIGNED,
            comment="Credit comment",
        )
        magic_mixer.blend(
            core.features.bcm.BudgetLineItem,
            campaign=campaign,
            credit=credit,
            start_date=datetime.date.today() + datetime.timedelta(1),
            end_date=datetime.date.today() + datetime.timedelta(5),
            created_by=self.user,
            amount=10,
            margin=decimal.Decimal("0.2500"),
        )

        r = self.client.get(reverse("restapi.credit.internal:credits_details", kwargs={"credit_id": credit.id}))
        resp_json = self.assertResponseValid(r)

        self.assertEqual(resp_json["data"]["agencyId"], str(agency_one.id))
        self.assertEqual(resp_json["data"]["accountId"], None)

        put_data = resp_json["data"].copy()
        put_data["agencyId"] = str(agency_two.id)

        r = self.client.put(
            reverse("restapi.credit.internal:credits_details", kwargs={"credit_id": credit.id}),
            data=put_data,
            format="json",
        )
        resp_json = self.assertResponseError(r, "ValidationError")

        error_message = "Credit line item is used outside of the scope of {agency_name} agency. To change the scope of the credit line item to {agency_name} stop using it on other agencies (and their accounts, campaigns and ad groups) and try again.".format(
            agency_name=agency_two.name
        )
        self.assertIn(error_message, resp_json["details"]["agencyId"])

    @mock.patch("core.features.bcm.bcm_slack.log_to_slack")
    def test_post(self, mock_log_to_slack):
        agency = magic_mixer.blend(core.models.Agency, users=[self.user])

        post_data = {
            "status": dash.constants.CreditLineItemStatus.get_name(dash.constants.CreditLineItemStatus.SIGNED),
            "agencyId": str(agency.id),
            "startDate": self.normalize(datetime.date.today()),
            "endDate": self.normalize(datetime.date.today() + datetime.timedelta(30)),
            "amount": "100",
            "licenseFee": "30",
            "currency": dash.constants.Currency.get_name(dash.constants.Currency.EUR),
            "comment": "Extra credit",
        }

        r = self.client.post(reverse("restapi.credit.internal:credits_list"), data=post_data, format="json")
        resp_json = self.assertResponseValid(r, data_type=dict, status_code=201)

        self.assertIsNotNone(resp_json["data"]["id"])
        self.assertIsNotNone(resp_json["data"]["createdOn"])
        self.assertEqual(
            resp_json["data"]["status"],
            dash.constants.CreditLineItemStatus.get_name(dash.constants.CreditLineItemStatus.SIGNED),
        )
        self.assertEqual(resp_json["data"]["agencyId"], str(agency.id))
        self.assertIsNone(resp_json["data"]["accountId"])
        self.assertIsNotNone(resp_json["data"]["startDate"])
        self.assertIsNotNone(resp_json["data"]["endDate"])
        self.assertIsNotNone(resp_json["data"]["createdBy"])
        self.assertEqual(resp_json["data"]["currency"], dash.constants.Currency.get_name(dash.constants.Currency.EUR))
        self.assertEqual(resp_json["data"]["licenseFee"], "30")
        self.assertIsNotNone(resp_json["data"]["flatFee"])
        self.assertEqual(resp_json["data"]["comment"], "Extra credit")
        self.assertEqual(resp_json["data"]["isAvailable"], True)
        self.assertEqual(resp_json["data"]["numOfBudgets"], 0)

    @mock.patch("core.features.bcm.bcm_slack.log_to_slack")
    def test_list_budgets(self, mock_log_to_slack):
        agency = magic_mixer.blend(core.models.Agency)
        account = magic_mixer.blend(core.models.Account, agency=agency, users=[self.user])
        campaign = magic_mixer.blend(
            core.models.Campaign, account=account, name="Test campaign", type=dash.constants.CampaignType.CONTENT
        )
        credit = magic_mixer.blend(
            core.features.bcm.CreditLineItem,
            account=account,
            start_date=datetime.date.today(),
            end_date=datetime.date.today() + datetime.timedelta(30),
            amount=200000,
            currency=dash.constants.Currency.USD,
            status=dash.constants.CreditLineItemStatus.SIGNED,
            comment="Credit comment",
        )

        budgets = magic_mixer.cycle(10).blend(
            core.features.bcm.BudgetLineItem,
            campaign=campaign,
            credit=credit,
            start_date=datetime.date.today() + datetime.timedelta(1),
            end_date=datetime.date.today() + datetime.timedelta(5),
            created_by=self.user,
            amount=10000,
            margin=decimal.Decimal("0.2500"),
        )

        r = self.client.get(reverse("restapi.credit.internal:credit_budgets_list", kwargs={"credit_id": credit.id}))
        resp_json = self.assertResponseValid(r, data_type=list)
        self.assertEqual(len(resp_json["data"]), 10)

        budgets_ids = sorted([item.id for item in budgets])
        resp_json_budgets_ids = sorted([int(item.get("id")) for item in resp_json["data"]])
        self.assertEqual(budgets_ids, resp_json_budgets_ids)
