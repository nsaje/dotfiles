from restapi.common.views_base_test import RESTAPITest
from django.urls import reverse

import dash.models
import datetime


class AccountCreditRefundTest(RESTAPITest):
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
        refund_db = dash.models.RefundLineItem.objects.get(pk=refund["id"])
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
            reverse("accounts_credits_refunds_details", kwargs={"account_id": 186, "credit_id": 861, "refund_id": 777})
        )
        resp_json = self.assertResponseValid(r)
        self.validate_against_db(resp_json["data"])

    def test_refund_get_doesnt_exist(self):
        r = self.client.get(
            reverse("accounts_credits_refunds_details", kwargs={"account_id": 186, "credit_id": 861, "refund_id": 7})
        )
        self.assertResponseError(r, "DoesNotExist")

    def test_refund_get_account_doesnt_exist(self):
        r = self.client.get(
            reverse("accounts_credits_refunds_details", kwargs={"account_id": 123, "credit_id": 861, "refund_id": 777})
        )
        self.assertResponseError(r, "MissingDataError")

    def test_account_credits_list(self):
        r = self.client.get(reverse("accounts_credits_refunds_list", kwargs={"account_id": 186, "credit_id": 861}))
        resp_json = self.assertResponseValid(r, data_type=list)
        for item in resp_json["data"]:
            self.validate_against_db(item)

    def test_account_credits_list_all(self):
        r = self.client.get(reverse("accounts_credits_refunds_list_all", kwargs={"account_id": 186}))
        resp_json = self.assertResponseValid(r, data_type=list)
        for item in resp_json["data"]:
            self.validate_against_db(item)

    def test_refund_post(self):
        new_refund = self.refund_repr(account_id=186, credit_id=861, amount=0)
        del new_refund["id"]
        r = self.client.post(
            reverse("accounts_credits_refunds_list", kwargs={"account_id": 186, "credit_id": 861}),
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
        new_refund = self.refund_repr()
        del new_refund["id"]
        r = self.client.post(
            reverse("accounts_credits_refunds_list", kwargs={"account_id": 186, "credit_id": 861}),
            data=new_refund,
            format="json",
        )
        self.assertResponseError(r, "ValidationError")

    def test_refund_post_comment_fail(self):
        new_refund = self.refund_repr(comment="")
        del new_refund["id"]
        r = self.client.post(
            reverse("accounts_credits_refunds_list", kwargs={"account_id": 186, "credit_id": 861}),
            data=new_refund,
            format="json",
        )
        self.assertResponseError(r, "ValidationError")

    def test_refund_post_date_fail(self):
        new_refund = self.refund_repr(start_date=datetime.date(2014, 1, 1))
        del new_refund["id"]
        r = self.client.post(
            reverse("accounts_credits_refunds_list", kwargs={"account_id": 186, "credit_id": 861}),
            data=new_refund,
            format="json",
        )
        self.assertResponseError(r, "ValidationError")

    def test_refund_delete(self):
        r = self.client.delete(
            reverse("accounts_credits_refunds_details", kwargs={"account_id": 186, "credit_id": 861, "refund_id": 777})
        )
        self.assertEqual(r.status_code, 204)
        r = self.client.get(
            reverse("accounts_credits_refunds_details", kwargs={"account_id": 186, "credit_id": 861, "refund_id": 777})
        )
        self.assertResponseError(r, "DoesNotExist")
