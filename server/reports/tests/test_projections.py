import datetime
from decimal import Decimal

from django import test

import dash.models
import dash.constants
import reports.models
import reports.projections
import utils.dates_helper


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
            'pacing': Decimal('2.489322757779133618059792556'),
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
            'pacing': Decimal('2.090163934426229508196721311'),
            'media_spend_projection': Decimal('9568.627450980392156862745099'),
            'allocated_total_budget': Decimal('11960.78431372549019607843137'),
            'license_fee_projection': Decimal('2000.0010'),
        })

        self.assertEqual(stats.row(2), {
            'ideal_media_spend': Decimal('3250.000000000000000000000000'),
            'attributed_media_spend': Decimal('10000.0000'),
            'allocated_media_budget': Decimal('6500.000000000000000000000001'),
            'pacing': Decimal('3.076923076923076923076923077'),
            'media_spend_projection': Decimal('6500.000000000000000000000001'),
            'allocated_total_budget': Decimal('10000.00000000000000000000000'),
            'license_fee_projection': Decimal('2000.0010')}
        )

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
            'pacing': Decimal('5.731717106847555591233844422'),
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
            'pacing': Decimal('4.567553735926305015353121802'),
            'media_spend_projection': Decimal('7662.745098039215686274509805'),
            'allocated_total_budget': Decimal('9578.431372549019607843137256'),
            'license_fee_projection': Decimal('1915.686274509803921568627451'),
        })

        self.assertEqual(stats.row(2), {
            'ideal_media_spend': Decimal('1300.000000000000000000000000'),
            'attributed_media_spend': Decimal('10000.0000'),
            'allocated_media_budget': Decimal('4550.000000000000000000000001'),
            'pacing': Decimal('7.692307692307692307692307692'),
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
                         Decimal('2.583543505674653215636822194'))
        self.assertEqual(stats.total('media_spend_projection'),
                         Decimal('16068.62745098039215686274510'))
        self.assertEqual(stats.total('allocated_total_budget'),
                         Decimal('21960.78431372549019607843137'))
        self.assertEqual(stats.total('license_fee_projection'),
                         Decimal('4000.0020'))
