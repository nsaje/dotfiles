import datetime
from decimal import Decimal

from django import test

import dash.models
import dash.constants
import reports.models
import reports.projections
import utils.dates_helper

from django.test.client import RequestFactory
from zemauth.models import User


class ProjectionsTestCase(test.TestCase):
    fixtures = ['test_projections']

    def setUp(self):
        self.today = datetime.date(2015, 11, 15)

    def _create_statement(self, budget, date, media=500, data=500, fee=100):
        reports.models.BudgetDailyStatement.objects.create(
            budget=budget,
            date=date,
            media_spend_nano=media * dash.models.TO_NANO_MULTIPLIER,
            data_spend_nano=data * dash.models.TO_NANO_MULTIPLIER,
            license_fee_nano=fee * dash.models.TO_NANO_MULTIPLIER,
        )

    def _create_batch_statements(self, budgets, start_date):
        for date in utils.dates_helper.date_range(start_date, self.today):
            for budget in budgets:
                if budget.state(date) != dash.constants.BudgetLineItemState.ACTIVE:
                    continue
                self._create_statement(budget, date)

    def test_running_half_month(self):
        start_date, end_date = datetime.date(2015, 11, 1), datetime.date(2015, 11, 30)
        self._create_batch_statements(
            dash.models.BudgetLineItem.objects.all(),
            start_date
        )
        stats = reports.projections.BudgetProjections(start_date, end_date, 'account',
                                                      projection_date=self.today)

        self.assertEqual(stats.row(1), {
            'total_fee_projection': Decimal('3999.9990'),
            'ideal_media_spend': Decimal('8034.313725490196078431372550'),
            'attributed_media_spend': Decimal('20000.0000'),
            'allocated_media_budget': Decimal('16068.62745098039215686274510'),
            'pacing': Decimal('248.9322757779133618059792556'),
            'total_fee': Decimal('2000.0000'),
            'flat_fee': Decimal('0.0'),
            'media_spend_projection': Decimal('16068.62745098039215686274510'),
            'allocated_total_budget': Decimal('21960.78431372549019607843137'),
            'license_fee_projection': Decimal('3999.9990'),
            'attributed_license_fee': Decimal('2000.0000'),
        })

        stats = reports.projections.BudgetProjections(start_date, end_date, 'campaign',
                                                      projection_date=self.today)

        self.assertEqual(stats.row(1), {
            'ideal_media_spend': Decimal('4784.313725490196078431372549'),
            'attributed_media_spend': Decimal('10000.0000'),
            'allocated_media_budget': Decimal('9568.627450980392156862745099'),
            'pacing': Decimal('209.0163934426229508196721311'),
            'media_spend_projection': Decimal('9568.627450980392156862745099'),
            'allocated_total_budget': Decimal('11960.78431372549019607843137'),
            'license_fee_projection': Decimal('2000.0010'),
        })

        self.assertEqual(stats.row(2), {
            'ideal_media_spend': Decimal('3250.000000000000000000000000'),
            'attributed_media_spend': Decimal('10000.0000'),
            'allocated_media_budget': Decimal('6500.000000000000000000000001'),
            'pacing': Decimal('307.6923076923076923076923077'),
            'media_spend_projection': Decimal('6500.000000000000000000000001'),
            'allocated_total_budget': Decimal('10000.00000000000000000000000'),
            'license_fee_projection': Decimal('2000.0010')}
        )


    def test_running_half_month_agency_flat_fee(self):
        rf = RequestFactory()
        r = rf.get('')
        r.user = User.objects.get(pk=1)
        agency = dash.models.Agency(
            name="test agency"
        )
        agency.save(r)

        start_date, end_date = datetime.date(2015, 11, 1), datetime.date(2015, 11, 30)

        credit = dash.models.CreditLineItem(
            agency=agency,
            start_date=start_date,
            end_date=end_date,
            amount=10000,
            flat_fee_cc=5000 * 1e4,
            flat_fee_start_date=start_date,
            flat_fee_end_date=end_date,
            status=dash.constants.CreditLineItemStatus.SIGNED,
            created_by=r.user,
        )
        credit.save()

        account = dash.models.Account.objects.get(pk=1)
        account.agency = agency
        account.save(r)

        self._create_batch_statements(
            dash.models.BudgetLineItem.objects.all(),
            start_date
        )
        stats = reports.projections.BudgetProjections(start_date, end_date, 'account',
                                                      projection_date=self.today)

        self.assertEqual(stats.row(1)['flat_fee'], 5000)
        self.assertFalse('flat_fee' in stats.row(2))

    def test_running_five_days(self):
        start_date, end_date = datetime.date(2015, 11, 10), datetime.date(2015, 11, 30)
        self._create_batch_statements(
            dash.models.BudgetLineItem.objects.all(),
            start_date
        )
        stats = reports.projections.BudgetProjections(start_date, end_date, 'account',
                                                      projection_date=self.today)

        self.assertEqual(stats.row(1), {
            'total_fee_projection': Decimal('4365.68627450980392156862745'),
            'ideal_media_spend': Decimal('3489.355742296918767507002803'),
            'attributed_media_spend': Decimal('20000.0000'),
            'allocated_media_budget': Decimal('12212.74509803921568627450981'),
            'pacing': Decimal('573.1717106847555591233844422'),
            'total_fee': Decimal('2000.0000'),
            'flat_fee': Decimal('0.0'),
            'media_spend_projection': Decimal('12212.74509803921568627450981'),
            'allocated_total_budget': Decimal('16578.43137254901960784313726'),
            'license_fee_projection': Decimal('4365.68627450980392156862745'),
            'attributed_license_fee': Decimal('2000.0000'),
        })

        stats = reports.projections.BudgetProjections(start_date, end_date, 'campaign',
                                                      projection_date=self.today)

        self.assertEqual(stats.row(1), {
            'ideal_media_spend': Decimal('2189.355742296918767507002801'),
            'attributed_media_spend': Decimal('10000.0000'),
            'allocated_media_budget': Decimal('7662.745098039215686274509805'),
            'pacing': Decimal('456.7553735926305015353121802'),
            'media_spend_projection': Decimal('7662.745098039215686274509805'),
            'allocated_total_budget': Decimal('9578.431372549019607843137256'),
            'license_fee_projection': Decimal('1915.686274509803921568627451'),
        })

        self.assertEqual(stats.row(2), {
            'ideal_media_spend': Decimal('1300.000000000000000000000000'),
            'attributed_media_spend': Decimal('10000.0000'),
            'allocated_media_budget': Decimal('4550.000000000000000000000001'),
            'pacing': Decimal('769.2307692307692307692307692'),
            'media_spend_projection': Decimal('4550.000000000000000000000001'),
            'allocated_total_budget': Decimal('7000.000000000000000000000002'),
            'license_fee_projection': Decimal('2450.000000000000000000000001'),
        })

    def test_totals(self):
        start_date, end_date = datetime.date(2015, 11, 1), datetime.date(2015, 11, 30)
        self._create_batch_statements(
            dash.models.BudgetLineItem.objects.all(),
            start_date
        )
        stats = reports.projections.BudgetProjections(start_date, end_date, 'campaign',
                                                      projection_date=self.today)

        self.assertEqual(stats.total('ideal_media_spend'),
                         Decimal('8034.313725490196078431372549'))
        self.assertEqual(stats.total('attributed_media_spend'),
                         Decimal('20000.0000'))
        self.assertEqual(stats.total('allocated_media_budget'),
                         Decimal('16068.62745098039215686274510'))
        self.assertEqual(stats.total('pacing'),
                         Decimal('248.9322757779133618059792556'))
        self.assertEqual(stats.total('media_spend_projection'),
                         Decimal('16068.62745098039215686274510'))
        self.assertEqual(stats.total('allocated_total_budget'),
                         Decimal('21960.78431372549019607843137'))
        self.assertEqual(stats.total('license_fee_projection'),
                         Decimal('4000.0020'))
