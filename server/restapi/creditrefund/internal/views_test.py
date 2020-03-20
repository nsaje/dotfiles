import datetime

import mock
from django.urls import reverse

import core.features.bcm
import core.features.bcm.refund_line_item
import core.models
import dash.constants
import utils.test_helper
from restapi.common.views_base_test import RESTAPITest
from utils.magic_mixer import magic_mixer


class CreditRefundViewSetTest(RESTAPITest):
    @classmethod
    def refund_repr(
        cls,
        id=123,
        account_id=123,
        credit_id=123,
        start_date=datetime.date(2018, 4, 1),
        end_date=datetime.date(2018, 4, 30),
        amount=500,
        effective_margin="0",
        comment="test",
        created_by="test@test.com",
        created_dt=datetime.datetime.now(),
    ):
        return cls.normalize(
            {
                "id": str(id),
                "accountId": str(account_id),
                "creditId": str(credit_id),
                "startDate": start_date,
                "endDate": end_date,
                "amount": amount,
                "effectiveMargin": effective_margin,
                "comment": comment,
                "createdBy": created_by,
                "createdDt": created_dt,
            }
        )

    def validate_against_db(self, refund):
        refund_db = core.features.bcm.refund_line_item.RefundLineItem.objects.get(pk=refund["id"])
        expected = self.refund_repr(
            id=str(refund_db.id),
            account_id=str(refund_db.account.id),
            credit_id=str(refund_db.credit.id),
            start_date=refund_db.start_date,
            end_date=refund_db.end_date,
            amount=refund_db.amount,
            effective_margin=refund_db.effective_margin.normalize(),
            comment=refund_db.comment,
            created_by=str(refund_db.created_by),
            created_dt=refund_db.created_dt,
        )
        self.assertEqual(expected, refund)

    def test_refund_get(self):
        r = self.client.get(
            reverse(
                "restapi.creditrefund.internal:credits_refunds_details", kwargs={"credit_id": 861, "refund_id": 777}
            )
        )
        resp_json = self.assertResponseValid(r)
        self.validate_against_db(resp_json["data"])

    def test_refund_get_doesnt_exist(self):
        r = self.client.get(
            reverse("restapi.creditrefund.internal:credits_refunds_details", kwargs={"credit_id": 861, "refund_id": 7})
        )
        self.assertResponseError(r, "MissingDataError")

    def test_credits_list(self):
        r = self.client.get(reverse("restapi.creditrefund.internal:credits_refunds_list", kwargs={"credit_id": 861}))
        resp_json = self.assertResponseValid(r, data_type=list)
        for item in resp_json["data"]:
            self.validate_against_db(item)

    def test_credits_list_all(self):
        r = self.client.get(reverse("restapi.creditrefund.internal:credits_refunds_list_all"), {"accountId": 186})
        resp_json = self.assertResponseValid(r, data_type=list)
        for item in resp_json["data"]:
            self.validate_against_db(item)

    def test_refund_post(self):
        new_refund = self.refund_repr(account_id=186, credit_id=861, amount=0)
        del new_refund["id"]
        r = self.client.post(
            reverse("restapi.creditrefund.internal:credits_refunds_list", kwargs={"credit_id": 861}),
            data=new_refund,
            format="json",
        )
        resp_json = self.assertResponseValid(r, data_type=dict, status_code=201)
        self.validate_against_db(resp_json["data"])
        new_refund["id"] = resp_json["data"]["id"]
        new_refund["createdBy"] = resp_json["data"]["createdBy"]
        new_refund["createdDt"] = resp_json["data"]["createdDt"]
        self.assertEqual(resp_json["data"], new_refund)

    def test_refund_post_amount_fail(self):
        new_refund = self.refund_repr(account_id=186, credit_id=861)
        del new_refund["id"]
        r = self.client.post(
            reverse("restapi.creditrefund.internal:credits_refunds_list", kwargs={"credit_id": 861}),
            data=new_refund,
            format="json",
        )
        self.assertResponseError(r, "ValidationError")

    def test_refund_post_comment_fail(self):
        new_refund = self.refund_repr(account_id=186, credit_id=861, comment="")
        del new_refund["id"]
        r = self.client.post(
            reverse("restapi.creditrefund.internal:credits_refunds_list", kwargs={"credit_id": 861}),
            data=new_refund,
            format="json",
        )
        self.assertResponseError(r, "ValidationError")

    def test_refund_post_date_fail(self):
        new_refund = self.refund_repr(account_id=186, credit_id=861, start_date=datetime.date(2014, 1, 1))
        del new_refund["id"]
        r = self.client.post(
            reverse("restapi.creditrefund.internal:credits_refunds_list", kwargs={"credit_id": 861}),
            data=new_refund,
            format="json",
        )
        self.assertResponseError(r, "ValidationError")

    def test_refund_post_missing_account(self):
        new_refund = self.refund_repr(credit_id=861)
        del new_refund["id"]
        del new_refund["accountId"]
        r = self.client.post(
            reverse("restapi.creditrefund.internal:credits_refunds_list", kwargs={"credit_id": 861}),
            data=new_refund,
            format="json",
        )
        self.assertResponseError(r, "ValidationError")

    def test_refund_delete(self):
        r = self.client.delete(
            reverse(
                "restapi.creditrefund.internal:credits_refunds_details", kwargs={"credit_id": 861, "refund_id": 777}
            )
        )
        self.assertEqual(r.status_code, 204)
        r = self.client.get(
            reverse(
                "restapi.creditrefund.internal:credits_refunds_details", kwargs={"credit_id": 861, "refund_id": 777}
            )
        )
        self.assertResponseError(r, "MissingDataError")

    def test_get_refund_no_access(self):
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
        refund = magic_mixer.blend(core.features.bcm.refund_line_item.RefundLineItem, account=account, credit=credit)

        r = self.client.get(
            reverse(
                "restapi.creditrefund.internal:credits_refunds_details",
                kwargs={"credit_id": credit.id, "refund_id": refund.id},
            )
        )
        self.assertResponseError(r, "AuthorizationError")

    def test_get_refund_no_permission(self):
        utils.test_helper.remove_permissions(self.user, ["can_manage_credit_refunds"])
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
        refund = magic_mixer.blend(core.features.bcm.refund_line_item.RefundLineItem, account=account, credit=credit)

        r = self.client.get(
            reverse(
                "restapi.creditrefund.internal:credits_refunds_details",
                kwargs={"credit_id": credit.id, "refund_id": refund.id},
            )
        )
        self.assertEqual(r.status_code, 403)
        resp_json = self.assertResponseError(r, "PermissionDenied")
        self.assertEqual(
            resp_json,
            {"errorCode": "PermissionDenied", "details": "You do not have permission to perform this action."},
        )

    @mock.patch("core.features.bcm.bcm_slack.log_to_slack")
    def test_list_pagination_with_agency(self, mock_log_to_slack):
        agency = magic_mixer.blend(core.models.Agency, users=[self.user])
        account_one = magic_mixer.blend(core.models.Account, agency=agency, users=[self.user])
        account_two = magic_mixer.blend(core.models.Account, agency=agency, users=[self.user])
        credit = magic_mixer.blend(
            core.features.bcm.CreditLineItem,
            agency=agency,
            account=None,
            start_date=datetime.date.today(),
            end_date=datetime.date.today() + datetime.timedelta(30),
            amount=200000,
            currency=dash.constants.Currency.USD,
            status=dash.constants.CreditLineItemStatus.SIGNED,
        )
        # refunds for account_one
        account_one_refunds = magic_mixer.cycle(10).blend(
            core.features.bcm.refund_line_item.RefundLineItem, account=account_one, credit=credit
        )
        # refunds for account_two
        account_two_refunds = magic_mixer.cycle(10).blend(
            core.features.bcm.refund_line_item.RefundLineItem, account=account_two, credit=credit
        )

        r = self.client.get(
            reverse("restapi.creditrefund.internal:credits_refunds_list_all"),
            {"agencyId": agency.id, "offset": 0, "limit": 30},
        )
        resp_json = self.assertResponseValid(r, data_type=list)
        self.assertEqual(resp_json["count"], 20)
        self.assertIsNone(resp_json["previous"])
        self.assertIsNone(resp_json["next"])

        refund_ids = sorted([refund.id for refund in account_one_refunds + account_two_refunds])
        resp_json_ids = sorted([int(item.get("id")) for item in resp_json["data"]])
        self.assertEqual(refund_ids, resp_json_ids)

    @mock.patch("core.features.bcm.bcm_slack.log_to_slack")
    def test_list_pagination_with_account(self, mock_log_to_slack):
        agency = magic_mixer.blend(core.models.Agency, users=[self.user])
        account_one = magic_mixer.blend(core.models.Account, agency=agency, users=[self.user])
        account_two = magic_mixer.blend(core.models.Account, agency=agency, users=[self.user])
        credit = magic_mixer.blend(
            core.features.bcm.CreditLineItem,
            agency=agency,
            account=None,
            start_date=datetime.date.today(),
            end_date=datetime.date.today() + datetime.timedelta(30),
            amount=200000,
            currency=dash.constants.Currency.USD,
            status=dash.constants.CreditLineItemStatus.SIGNED,
        )
        # refunds for account_one
        account_one_refunds = magic_mixer.cycle(10).blend(
            core.features.bcm.refund_line_item.RefundLineItem, account=account_one, credit=credit
        )
        # refunds for account_two
        magic_mixer.cycle(10).blend(
            core.features.bcm.refund_line_item.RefundLineItem, account=account_two, credit=credit
        )

        r = self.client.get(
            reverse("restapi.creditrefund.internal:credits_refunds_list_all"),
            {"accountId": account_one.id, "offset": 0, "limit": 30},
        )
        resp_json = self.assertResponseValid(r, data_type=list)
        self.assertEqual(resp_json["count"], 10)
        self.assertIsNone(resp_json["previous"])
        self.assertIsNone(resp_json["next"])

        refund_ids = sorted([refund.id for refund in account_one_refunds])
        resp_json_ids = sorted([int(item.get("id")) for item in resp_json["data"]])
        self.assertEqual(refund_ids, resp_json_ids)

    @mock.patch("core.features.bcm.bcm_slack.log_to_slack")
    def test_list_pagination_with_credit(self, mock_log_to_slack):
        agency = magic_mixer.blend(core.models.Agency, users=[self.user])
        account_one = magic_mixer.blend(core.models.Account, agency=agency, users=[self.user])
        credit_one = magic_mixer.blend(
            core.features.bcm.CreditLineItem,
            agency=None,
            account=account_one,
            start_date=datetime.date.today(),
            end_date=datetime.date.today() + datetime.timedelta(30),
            amount=200000,
            currency=dash.constants.Currency.USD,
            status=dash.constants.CreditLineItemStatus.SIGNED,
        )
        credit_two = magic_mixer.blend(
            core.features.bcm.CreditLineItem,
            agency=None,
            account=account_one,
            start_date=datetime.date.today(),
            end_date=datetime.date.today() + datetime.timedelta(30),
            amount=200000,
            currency=dash.constants.Currency.USD,
            status=dash.constants.CreditLineItemStatus.SIGNED,
        )
        # refunds for account_one
        credit_one_refunds = magic_mixer.cycle(10).blend(
            core.features.bcm.refund_line_item.RefundLineItem, account=account_one, credit=credit_one
        )
        # refunds for account_two
        magic_mixer.cycle(10).blend(
            core.features.bcm.refund_line_item.RefundLineItem, account=account_one, credit=credit_two
        )

        r = self.client.get(
            reverse("restapi.creditrefund.internal:credits_refunds_list", kwargs={"credit_id": credit_one.id}),
            {"offset": 0, "limit": 30},
        )
        resp_json = self.assertResponseValid(r, data_type=list)
        self.assertEqual(resp_json["count"], 10)
        self.assertIsNone(resp_json["previous"])
        self.assertIsNone(resp_json["next"])

        refund_ids = sorted([refund.id for refund in credit_one_refunds])
        resp_json_ids = sorted([int(item.get("id")) for item in resp_json["data"]])
        self.assertEqual(refund_ids, resp_json_ids)

    @mock.patch("core.features.bcm.bcm_slack.log_to_slack")
    def test_post_invalid_account(self, mock_log_to_slack):
        agency = magic_mixer.blend(core.models.Agency, users=[self.user])
        account_one = magic_mixer.blend(core.models.Account, agency=agency, users=[self.user])
        account_two = magic_mixer.blend(core.models.Account, agency=agency, users=[self.user])
        credit = magic_mixer.blend(
            core.features.bcm.CreditLineItem,
            agency=None,
            account=account_one,
            start_date=datetime.date.today(),
            end_date=datetime.date.today() + datetime.timedelta(30),
            amount=200000,
            currency=dash.constants.Currency.USD,
            status=dash.constants.CreditLineItemStatus.SIGNED,
        )

        new_refund = self.refund_repr(account_id=account_two.id, credit_id=credit.id, amount=0)
        del new_refund["id"]
        r = self.client.post(
            reverse("restapi.creditrefund.internal:credits_refunds_list", kwargs={"credit_id": credit.id}),
            data=new_refund,
            format="json",
        )
        self.assertResponseError(r, "ValidationError")
