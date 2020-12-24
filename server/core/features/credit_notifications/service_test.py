import datetime

import mock
from django.test import TestCase
from parameterized import param
from parameterized import parameterized

import core.features.bcm
import dash.constants
import zemauth.models
from utils import test_helper
from utils.magic_mixer import magic_mixer

from . import models
from . import service

FUNCTIONAL_DECLARATIONS = [
    param(
        "80_percent_to_be_sent",
        budget_spend_percent=0.85,
        sent_80_percent=False,
        sent_90_percent=False,
        expect_send_email_80_percent=True,
        expect_send_email_90_percent=False,
    ),
    param(
        "80_percent_already_sent",
        budget_spend_percent=0.85,
        sent_80_percent=True,
        sent_90_percent=False,
        expect_send_email_80_percent=False,
        expect_send_email_90_percent=False,
    ),
    param(
        "90_percent_to_be_sent",
        budget_spend_percent=0.95,
        sent_80_percent=True,
        sent_90_percent=False,
        expect_send_email_80_percent=False,
        expect_send_email_90_percent=True,
    ),
    param(
        "90_percent_already_sent",
        budget_spend_percent=0.95,
        sent_80_percent=True,
        sent_90_percent=True,
        expect_send_email_80_percent=False,
        expect_send_email_90_percent=False,
    ),
    param(
        "90_percent_already_sent_less_spend",
        budget_spend_percent=0.85,
        sent_80_percent=True,
        sent_90_percent=True,
        expect_send_email_80_percent=False,
        expect_send_email_90_percent=False,
    ),
    param(
        "90_percent_unset",
        budget_spend_percent=0.85,
        sent_80_percent=True,
        sent_90_percent=True,
        expect_send_email_80_percent=False,
        expect_send_email_90_percent=False,
    ),
    param(
        "80_percent_unset",
        budget_spend_percent=0.5,
        sent_80_percent=True,
        sent_90_percent=True,
        expect_send_email_80_percent=False,
        expect_send_email_90_percent=False,
    ),
]

IS_AGENCY_LEVEL_DECLARATIONS = [param("agency", is_agency_level=True), param("account", is_agency_level=False)]


TEST_CASES = test_helper.params_cross_product(FUNCTIONAL_DECLARATIONS, IS_AGENCY_LEVEL_DECLARATIONS)


class CreditNotificationsTest(TestCase):
    maxDiff = None

    @parameterized.expand(TEST_CASES)
    @mock.patch.object(core.features.bcm.CreditLineItem, "get_total_budgets_spend")
    @mock.patch("utils.email_helper.send_official_email")
    def test_credit_notifications(
        self,
        _,
        mock_send_official_email,
        mock_get_total_budgets_spend,
        *,
        budget_spend_percent,
        sent_80_percent,
        sent_90_percent,
        expect_send_email_80_percent,
        expect_send_email_90_percent,
        is_agency_level,
    ):
        self._init_credit(is_agency_level)
        self._init_notifications(sent_80_percent, sent_90_percent)
        mock_get_total_budgets_spend.return_value = budget_spend_percent * self.credit.amount

        service.check_and_notify_depleting_credits()

        self.credit.refresh_from_db()
        self.assertEqual(budget_spend_percent > 0.8, self.credit.notifications.sent_80_percent)
        self.assertEqual(budget_spend_percent > 0.9, self.credit.notifications.sent_90_percent)
        self._assert_emails_sent(
            mock_send_official_email, is_agency_level, expect_send_email_80_percent, expect_send_email_90_percent
        )

    def _assert_emails_sent(
        self, mock_send_official_email, is_agency_level, expect_send_email_80_percent, expect_send_email_90_percent
    ):
        calls = [
            (
                call_args[1]["agency_or_user"],
                call_args[1]["recipient_list"],
                call_args[1]["subject"],
                call_args[1]["body"],
            )
            for call_args in mock_send_official_email.call_args_list
        ]

        expected_calls = []
        expected_recipients = [self.account_manager, self.sales_representative, self.cs_representative]
        agency_or_account = self.agency if is_agency_level else self.account
        if expect_send_email_80_percent:
            expected_calls.append(
                (
                    self.agency if is_agency_level else self.account.settings.default_account_manager,
                    [recipient.email for recipient in expected_recipients if recipient is not None],
                    "Less than 20% amount remaining on credit",
                    test_helper.SubstringMatcher("{} ({})".format(agency_or_account.name, agency_or_account.id)),
                )
            )
        if expect_send_email_90_percent:
            expected_calls.append(
                (
                    self.agency if is_agency_level else self.account.settings.default_account_manager,
                    [recipient.email for recipient in expected_recipients if recipient is not None],
                    "Less than 10% amount remaining on credit",
                    test_helper.SubstringMatcher("{} ({})".format(agency_or_account.name, agency_or_account.id)),
                )
            )
        self.assertCountEqual(calls, expected_calls)

    def _init_credit(self, is_agency_level):
        self.agency = None
        self.account = None

        if is_agency_level:
            self.account_manager = None
            self.sales_representative = magic_mixer.blend(zemauth.models.User, email="salesrepresentative@zemanta.com")
            self.cs_representative = magic_mixer.blend(zemauth.models.User, email="csrepresentative@zemanta.com")

            self.agency = magic_mixer.blend(
                core.models.Agency,
                sales_representative=self.sales_representative,
                cs_representative=self.cs_representative,
            )
        else:
            self.account = magic_mixer.blend(core.models.Account)

            self.account_manager = magic_mixer.blend(zemauth.models.User, email="accountmanager@zemanta.com")
            self.sales_representative = magic_mixer.blend(zemauth.models.User, email="salesrepresentative@zemanta.com")
            self.cs_representative = magic_mixer.blend(zemauth.models.User, email="csrepresentative@zemanta.com")
            self.account.settings.update(
                None,
                default_account_manager=self.account_manager,
                default_sales_representative=self.sales_representative,
                default_cs_representative=self.cs_representative,
            )

        self.credit = magic_mixer.blend(
            core.features.bcm.CreditLineItem,
            agency=self.agency,
            account=self.account,
            start_date=datetime.date.today(),
            end_date=datetime.date.today() + datetime.timedelta(30),
            amount=1000,
            currency=dash.constants.Currency.USD,
            status=dash.constants.CreditLineItemStatus.SIGNED,
            comment="Credit comment",
        )

    def _init_notifications(self, sent_80_percent, sent_90_percent):
        if not sent_80_percent and not sent_90_percent:
            return

        notifications = models.CreditNotifications.objects.create(credit=self.credit)
        notifications.unset_all()

        if sent_80_percent:
            notifications.set_sent_80_percent()

        if sent_90_percent:
            notifications.set_all()
