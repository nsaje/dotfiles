import datetime

import mock
from django.urls import reverse

import core.features.bcm
import core.features.bcm.refund_line_item
import core.models
import dash.constants
import utils.test_helper
from restapi.common.views_base_test_case import FutureRESTAPITestCase
from restapi.common.views_base_test_case import RESTAPITestCase
from utils.magic_mixer import magic_mixer
from zemauth.features.entity_permission import Permission


class LegacyCreditRefundViewSetTest(RESTAPITestCase):
    def setUp(self):
        super().setUp()
        self.account = self.mix_account(self.user, permissions=[Permission.READ, Permission.WRITE])
        self.credit = magic_mixer.blend(
            core.features.bcm.CreditLineItem,
            account=self.account,
            start_date=datetime.date.today(),
            end_date=datetime.date.today() + datetime.timedelta(30),
            amount=2000,
            currency=dash.constants.Currency.USD,
            status=dash.constants.CreditLineItemStatus.SIGNED,
        )

    @classmethod
    def refund_repr(
        cls,
        id=None,
        account_id=None,
        credit_id=None,
        start_date=None,
        end_date=None,
        amount=0,
        effective_margin="0",
        comment="test",
        created_by="test@test.com",
        created_dt=datetime.datetime.now(),
    ):
        return cls.normalize(
            {
                "id": str(id) if id is not None else None,
                "accountId": str(account_id) if account_id is not None else None,
                "creditId": str(credit_id) if credit_id is not None else None,
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
        refund = magic_mixer.blend(
            core.features.bcm.refund_line_item.RefundLineItem,
            account=self.account,
            credit=self.credit,
            created_by=self.user,
        )
        r = self.client.get(
            reverse(
                "restapi.creditrefund.internal:credits_refunds_details",
                kwargs={"credit_id": self.credit.id, "refund_id": refund.id},
            )
        )
        resp_json = self.assertResponseValid(r)
        self.validate_against_db(resp_json["data"])

    def test_refund_get_doesnt_exist(self):
        r = self.client.get(
            reverse(
                "restapi.creditrefund.internal:credits_refunds_details",
                kwargs={"credit_id": self.credit.id, "refund_id": 1234},
            )
        )
        self.assertResponseError(r, "MissingDataError")

    def test_credits_list(self):
        magic_mixer.cycle(5).blend(
            core.features.bcm.refund_line_item.RefundLineItem,
            account=self.account,
            credit=self.credit,
            created_by=self.user,
        )
        r = self.client.get(
            reverse("restapi.creditrefund.internal:credits_refunds_list", kwargs={"credit_id": self.credit.id})
        )
        resp_json = self.assertResponseValid(r, data_type=list)
        for item in resp_json["data"]:
            self.validate_against_db(item)

    def test_refund_get_invalid_params(self):
        r = self.client.get(
            reverse("restapi.creditrefund.internal:credits_refunds_list_all"), {"accountId": "NON-NUMERIC"}
        )
        resp_json = self.assertResponseError(r, "ValidationError")
        self.assertEqual({"accountId": ["Invalid format"]}, resp_json["details"])

    def test_refund_post(self):
        new_refund = self.refund_repr(
            account_id=self.account.id,
            credit_id=self.credit.id,
            start_date=datetime.date(self.credit.start_date.year, self.credit.start_date.month, 1),
            end_date=self.credit.end_date,
        )
        del new_refund["id"]
        r = self.client.post(
            reverse("restapi.creditrefund.internal:credits_refunds_list", kwargs={"credit_id": self.credit.id}),
            data=new_refund,
            format="json",
        )
        resp_json = self.assertResponseValid(r, data_type=dict, status_code=201)
        self.validate_against_db(resp_json["data"])

    def test_refund_post_amount_fail(self):
        new_refund = self.refund_repr(
            account_id=self.account.id,
            credit_id=self.credit.id,
            start_date=datetime.date(self.credit.start_date.year, self.credit.start_date.month, 1),
            end_date=self.credit.end_date,
            amount=500,
        )
        del new_refund["id"]
        r = self.client.post(
            reverse("restapi.creditrefund.internal:credits_refunds_list", kwargs={"credit_id": self.credit.id}),
            data=new_refund,
            format="json",
        )
        resp_json = self.assertResponseError(r, "ValidationError")
        self.assertIn("Total refunded amount exceeded total spend.", resp_json["details"]["amount"])

    def test_refund_post_comment_fail(self):
        new_refund = self.refund_repr(
            account_id=self.account.id,
            credit_id=self.credit.id,
            start_date=datetime.date(self.credit.start_date.year, self.credit.start_date.month, 1),
            end_date=self.credit.end_date,
            comment="",
        )
        del new_refund["id"]
        r = self.client.post(
            reverse("restapi.creditrefund.internal:credits_refunds_list", kwargs={"credit_id": self.credit.id}),
            data=new_refund,
            format="json",
        )
        resp_json = self.assertResponseError(r, "ValidationError")
        self.assertIn("This field may not be blank.", resp_json["details"]["comment"])

    def test_refund_post_date_fail(self):
        new_refund = self.refund_repr(
            account_id=self.account.id,
            credit_id=self.credit.id,
            start_date=datetime.date(self.credit.start_date.year, self.credit.start_date.month, 2),
            end_date=self.credit.end_date,
        )
        del new_refund["id"]
        r = self.client.post(
            reverse("restapi.creditrefund.internal:credits_refunds_list", kwargs={"credit_id": self.credit.id}),
            data=new_refund,
            format="json",
        )
        resp_json = self.assertResponseError(r, "ValidationError")
        self.assertIn("Start date has to be set on the first day of the month.", resp_json["details"]["startDate"])

    def test_refund_post_missing_account(self):
        new_refund = self.refund_repr(
            credit_id=self.credit.id,
            start_date=datetime.date(self.credit.start_date.year, self.credit.start_date.month, 1),
            end_date=self.credit.end_date,
        )
        del new_refund["id"]
        del new_refund["accountId"]
        r = self.client.post(
            reverse("restapi.creditrefund.internal:credits_refunds_list", kwargs={"credit_id": self.credit.id}),
            data=new_refund,
            format="json",
        )
        resp_json = self.assertResponseError(r, "ValidationError")
        self.assertIn("This field is required.", resp_json["details"]["accountId"])

    def test_refund_delete(self):
        refund = magic_mixer.blend(
            core.features.bcm.refund_line_item.RefundLineItem,
            account=self.account,
            credit=self.credit,
            start_date=datetime.date(self.credit.start_date.year, self.credit.start_date.month, 1),
            end_date=self.credit.end_date,
            ammount=0,
        )
        r = self.client.delete(
            reverse(
                "restapi.creditrefund.internal:credits_refunds_details",
                kwargs={"credit_id": self.credit.id, "refund_id": refund.id},
            )
        )
        self.assertEqual(r.status_code, 204)
        r = self.client.get(
            reverse(
                "restapi.creditrefund.internal:credits_refunds_details",
                kwargs={"credit_id": self.credit.id, "refund_id": refund.id},
            )
        )
        self.assertResponseError(r, "MissingDataError")

    def test_get_refund_no_access(self):
        account = magic_mixer.blend(core.models.Account)
        credit = magic_mixer.blend(
            core.features.bcm.CreditLineItem,
            account=account,
            start_date=datetime.date.today(),
            end_date=datetime.date.today() + datetime.timedelta(30),
        )
        refund = magic_mixer.blend(core.features.bcm.refund_line_item.RefundLineItem, account=account, credit=credit)
        r = self.client.get(
            reverse(
                "restapi.creditrefund.internal:credits_refunds_details",
                kwargs={"credit_id": credit.id, "refund_id": refund.id},
            )
        )
        self.assertResponseError(r, "MissingDataError")

    def test_get_refund_no_permission(self):
        utils.test_helper.remove_permissions(self.user, ["can_manage_credit_refunds"])
        account = self.mix_account(self.user, permissions=[Permission.READ])
        credit = magic_mixer.blend(
            core.features.bcm.CreditLineItem,
            account=account,
            start_date=datetime.date.today(),
            end_date=datetime.date.today() + datetime.timedelta(30),
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
        agency = self.mix_agency(self.user, permissions=[Permission.READ])
        account_one = magic_mixer.blend(core.models.Account, agency=agency)
        account_two = magic_mixer.blend(core.models.Account, agency=agency)
        credit = magic_mixer.blend(
            core.features.bcm.CreditLineItem,
            agency=agency,
            start_date=datetime.date.today(),
            end_date=datetime.date.today() + datetime.timedelta(30),
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
        agency = self.mix_agency(self.user, permissions=[Permission.READ])
        account_one = magic_mixer.blend(core.models.Account, agency=agency)
        account_two = magic_mixer.blend(core.models.Account, agency=agency)
        credit = magic_mixer.blend(
            core.features.bcm.CreditLineItem,
            agency=agency,
            start_date=datetime.date.today(),
            end_date=datetime.date.today() + datetime.timedelta(30),
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
        account = self.mix_account(self.user, permissions=[Permission.READ])
        credit_one = magic_mixer.blend(
            core.features.bcm.CreditLineItem,
            account=account,
            start_date=datetime.date.today(),
            end_date=datetime.date.today() + datetime.timedelta(30),
        )
        credit_two = magic_mixer.blend(
            core.features.bcm.CreditLineItem,
            account=account,
            start_date=datetime.date.today(),
            end_date=datetime.date.today() + datetime.timedelta(30),
        )
        # refunds for credit_one
        credit_one_refunds = magic_mixer.cycle(10).blend(
            core.features.bcm.refund_line_item.RefundLineItem, account=account, credit=credit_one
        )
        # refunds for credit_two
        magic_mixer.cycle(10).blend(
            core.features.bcm.refund_line_item.RefundLineItem, account=account, credit=credit_two
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
        account_one = self.mix_account(self.user, permissions=[Permission.READ, Permission.WRITE])
        account_two = self.mix_account(self.user, permissions=[Permission.READ, Permission.WRITE])
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
        new_refund = self.refund_repr(
            account_id=account_two.id,
            credit_id=credit.id,
            start_date=datetime.date(self.credit.start_date.year, self.credit.start_date.month, 1),
            end_date=self.credit.end_date,
        )
        del new_refund["id"]

        r = self.client.post(
            reverse("restapi.creditrefund.internal:credits_refunds_list", kwargs={"credit_id": credit.id}),
            data=new_refund,
            format="json",
        )
        resp_json = self.assertResponseError(r, "ValidationError")
        self.assertIn(
            "Refund account {} is not the same as credit account.".format(account_two.name),
            resp_json["details"]["accountId"],
        )


class CreditRefundViewSetTest(FutureRESTAPITestCase, LegacyCreditRefundViewSetTest):
    pass
