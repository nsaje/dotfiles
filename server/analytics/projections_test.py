import datetime
from decimal import Decimal

from django import test
import mock

import dash.models
import dash.constants
import analytics.projections
import utils.dates_helper
from utils.test_helper import fake_request

from django.test.client import RequestFactory
from zemauth.models import User

from utils import converters


class ProjectionsTestCase(test.TestCase):
    fixtures = ['test_projections']

    def setUp(self):
        self.today = datetime.date(2015, 11, 15)
        self.maxDiff = None

    def _create_statement(self, budget, date, media=500, data=500, fee=100, margin=0):
        dash.models.BudgetDailyStatement.objects.create(
            budget=budget,
            date=date,
            media_spend_nano=media * converters.DOLAR_TO_NANO,
            data_spend_nano=data * converters.DOLAR_TO_NANO,
            license_fee_nano=fee * converters.DOLAR_TO_NANO,
            margin_nano=margin * converters.DOLAR_TO_NANO,
        )

    def _create_batch_statements(self, budgets, start_date, end_date=None):
        for date in utils.dates_helper.date_range(start_date, end_date or self.today):
            for budget in budgets:
                if budget.state(date) != dash.constants.BudgetLineItemState.ACTIVE:
                    continue
                self._create_statement(budget, date)

    def test_first_of_month(self):
        start_date, end_date = datetime.date(2015, 11, 1), datetime.date(2015, 11, 30)

        self._create_batch_statements(
            dash.models.BudgetLineItem.objects.all(),
            start_date
        )
        with mock.patch('utils.dates_helper.local_today') as local_today:
            local_today.return_value = start_date
            stats = analytics.projections.BudgetProjections(start_date, end_date, 'account')

        self.assertEqual(stats.row(1), {
            'total_fee_projection': Decimal('5892.1569'),
            'ideal_media_spend': Decimal('535.6209'),
            'ideal_daily_media_spend': Decimal('535.6209'),
            'attributed_media_spend': Decimal('4000.0000'),
            'allocated_media_budget': Decimal('16068.6275'),
            'pacing': Decimal('746.7968'),
            'total_fee': Decimal('400.0000'),
            'flat_fee': Decimal('0.0000'),
            'media_spend_projection': Decimal('16068.6275'),
            'allocated_total_budget': Decimal('21960.7843'),
            'license_fee_projection': Decimal('5892.1569'),
            'attributed_license_fee': Decimal('400.0000')
        })

    def test_running_half_month(self):
        start_date, end_date = datetime.date(2015, 11, 1), datetime.date(2015, 11, 30)
        self._create_batch_statements(
            dash.models.BudgetLineItem.objects.all(),
            start_date
        )
        with mock.patch('utils.dates_helper.local_today') as local_today:
            local_today.return_value = self.today
            stats = analytics.projections.BudgetProjections(start_date, end_date, 'account',
                                                            projection_date=self.today)

        self.assertEqual(stats.row(1), {
            'total_fee_projection': Decimal('3999.9990'),
            'ideal_media_spend': Decimal('8034.3137'),
            'ideal_daily_media_spend': Decimal('535.6209'),
            'attributed_media_spend': Decimal('20000.0000'),
            'allocated_media_budget': Decimal('16068.6275'),
            'pacing': Decimal('248.9323'),
            'total_fee': Decimal('2000.0000'),
            'flat_fee': Decimal('0.0'),
            'media_spend_projection': Decimal('20000.0000'),
            'allocated_total_budget': Decimal('21960.7843'),
            'license_fee_projection': Decimal('3999.9990'),
            'attributed_license_fee': Decimal('2000.0000'),
        })

        with mock.patch('utils.dates_helper.local_today') as local_today:
            local_today.return_value = self.today
            stats = analytics.projections.BudgetProjections(start_date, end_date, 'campaign',
                                                            projection_date=self.today)

        self.assertEqual(stats.row(1), {
            'ideal_media_spend': Decimal('4784.3137'),
            'ideal_daily_media_spend': Decimal('318.9542'),
            'attributed_media_spend': Decimal('10000.0000'),
            'allocated_media_budget': Decimal('9568.6275'),
            'pacing': Decimal('209.0164'),
            'media_spend_projection': Decimal('10000.0000'),
            'allocated_total_budget': Decimal('11960.7843'),
            'license_fee_projection': Decimal('2000.0010'),
        })

        self.assertEqual(stats.row(2), {
            'ideal_media_spend': Decimal('3250.0000'),
            'ideal_daily_media_spend': Decimal('216.6667'),
            'attributed_media_spend': Decimal('10000.0000'),
            'allocated_media_budget': Decimal('6500.0000'),
            'pacing': Decimal('307.6923'),
            'media_spend_projection': Decimal('10000.0000'),
            'allocated_total_budget': Decimal('10000.0000'),
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

        cam = dash.models.Campaign(
            name='test campaign',
            account=account
        )
        cam.save(fake_request(User.objects.get(pk=1)))

        bud = dash.models.BudgetLineItem.objects.create_unsafe(
            campaign=cam,
            credit=credit,
            amount=100,
            start_date=start_date,
            end_date=end_date,
            created_by=User.objects.get(pk=1),
        )

        dash.models.BudgetDailyStatement.objects.create(
            budget=bud,
            date=start_date + datetime.timedelta(days=2),
            media_spend_nano=100,
            data_spend_nano=100,
            license_fee_nano=100,
            margin_nano=0,
        )

        self._create_batch_statements(
            dash.models.BudgetLineItem.objects.all(),
            start_date
        )

        with mock.patch('utils.dates_helper.local_today') as local_today:
            local_today.return_value = self.today
            stats = analytics.projections.BudgetProjections(
                start_date,
                end_date,
                'account',
                accounts=dash.models.Account.objects.filter(pk=1),
                projection_date=self.today
            )

        self.assertEqual(stats.row(1)['flat_fee'], 5000)
        self.assertFalse('flat_fee' in stats.row(2))

    def test_running_half_month_multi_account_agency_flat_fee(self):
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

        accounts = {}

        account = dash.models.Account.objects.get(pk=1)
        account.agency = agency
        account.save(r)

        # make up for additional accounts to add to agency
        for i in range(4):
            a = dash.models.Account(
                name='YATA - Yet Another Test Account {}'.format(i),
                agency=agency
            )
            a.save(r)
            accounts[i] = a

        self._create_batch_statements(
            dash.models.BudgetLineItem.objects.all(),
            start_date
        )

        with mock.patch('utils.dates_helper.local_today') as local_today:
            local_today.return_value = self.today
            stats = analytics.projections.BudgetProjections(
                start_date,
                end_date,
                'account',
                accounts=dash.models.Account.objects.filter(pk=1),
                projection_date=self.today
            )

        # agency level flat fee is distributed among all agency accounts with
        # spend
        self.assertEqual(stats.row(1)['flat_fee'], 5000)
        self.assertFalse('flat_fee' in stats.row(2))

        for i in range(4):
            credit = dash.models.CreditLineItem(
                account=accounts[i],
                start_date=start_date,
                end_date=end_date,
                amount=10000,
                status=dash.constants.CreditLineItemStatus.SIGNED,
                created_by=r.user,
            )
            credit.save()

            cam = dash.models.Campaign(
                name='test {}'.format(i),
                account=accounts[i]
            )
            cam.save(fake_request(User.objects.get(pk=1)))

            bud = dash.models.BudgetLineItem.objects.create_unsafe(
                campaign=cam,
                credit=credit,
                amount=100,
                start_date=start_date,
                end_date=end_date,
                created_by=User.objects.get(pk=1),
            )

            dash.models.BudgetDailyStatement.objects.create(
                budget=bud,
                date=start_date + datetime.timedelta(days=2),
                media_spend_nano=100,
                data_spend_nano=100,
                license_fee_nano=100,
                margin_nano=0,
            )

        with mock.patch('utils.dates_helper.local_today') as local_today:
            local_today.return_value = self.today
            stats = analytics.projections.BudgetProjections(
                start_date,
                end_date,
                'account',
                accounts=dash.models.Account.objects.all(),
                projection_date=self.today
            )

        # agency level flat fee is distributed among all agency accounts with
        # spend
        for i in range(1, 6):
            self.assertEqual(stats.row(i)['flat_fee'], 1000)

    def test_running_five_days(self):
        start_date, end_date = datetime.date(2015, 11, 10), datetime.date(2015, 11, 30)
        self._create_batch_statements(
            dash.models.BudgetLineItem.objects.all(),
            start_date
        )
        with mock.patch('utils.dates_helper.local_today') as local_today:
            local_today.return_value = self.today
            stats = analytics.projections.BudgetProjections(start_date, end_date, 'account',
                                                            projection_date=self.today)

        self.assertEqual(stats.row(1), {
            'total_fee_projection': Decimal('4365.6863'),
            'ideal_media_spend': Decimal('3489.3557'),
            'ideal_daily_media_spend': Decimal('581.5593'),
            'attributed_media_spend': Decimal('20000.0000'),
            'allocated_media_budget': Decimal('12212.7451'),
            'pacing': Decimal('573.1717'),
            'total_fee': Decimal('2000.0000'),
            'flat_fee': Decimal('0.0000'),
            'media_spend_projection': Decimal('20000.0000'),
            'allocated_total_budget': Decimal('16578.4314'),
            'license_fee_projection': Decimal('4365.6863'),
            'attributed_license_fee': Decimal('2000.0000'),
        })

        with mock.patch('utils.dates_helper.local_today') as local_today:
            local_today.return_value = self.today
            stats = analytics.projections.BudgetProjections(start_date, end_date, 'campaign',
                                                            projection_date=self.today)

        self.assertEqual(stats.row(1), {
            'ideal_media_spend': Decimal('2189.3557'),
            'ideal_daily_media_spend': Decimal('364.8926'),
            'attributed_media_spend': Decimal('10000.0000'),
            'allocated_media_budget': Decimal('7662.7451'),
            'pacing': Decimal('456.7554'),
            'media_spend_projection': Decimal('10000.0000'),
            'allocated_total_budget': Decimal('9578.4314'),
            'license_fee_projection': Decimal('1915.6863'),
        })

        self.assertEqual(stats.row(2), {
            'ideal_media_spend': Decimal('1300.0000'),
            'ideal_daily_media_spend': Decimal('216.6667'),
            'attributed_media_spend': Decimal('10000.0000'),
            'allocated_media_budget': Decimal('4550.0000'),
            'pacing': Decimal('769.2308'),
            'media_spend_projection': Decimal('10000.0000'),
            'allocated_total_budget': Decimal('7000.0000'),
            'license_fee_projection': Decimal('2450.0000'),
        })

    def test_totals(self):
        start_date, end_date = datetime.date(2015, 11, 1), datetime.date(2015, 11, 30)
        self._create_batch_statements(
            dash.models.BudgetLineItem.objects.all(),
            start_date
        )
        with mock.patch('utils.dates_helper.local_today') as local_today:
            local_today.return_value = self.today
            stats = analytics.projections.BudgetProjections(start_date, end_date, 'campaign',
                                                            projection_date=self.today)

        self.assertEqual(stats.total('ideal_media_spend'),
                         Decimal('8034.3137'))
        self.assertEqual(stats.total('ideal_daily_media_spend'),
                         Decimal('535.6209'))
        self.assertEqual(stats.total('attributed_media_spend'),
                         Decimal('20000.0000'))
        self.assertEqual(stats.total('allocated_media_budget'),
                         Decimal('16068.6275'))
        self.assertEqual(stats.total('pacing'),
                         Decimal('248.9323'))
        self.assertEqual(stats.total('media_spend_projection'),
                         Decimal('20000.0000'))
        self.assertEqual(stats.total('allocated_total_budget'),
                         Decimal('21960.7843'))
        self.assertEqual(stats.total('license_fee_projection'),
                         Decimal('4000.0020'))

    def test_past_projections(self):
        start_date, end_date = datetime.date(2015, 11, 1), datetime.date(2015, 11, 30)

        self._create_batch_statements(
            dash.models.BudgetLineItem.objects.all(),
            start_date,
            end_date,
        )
        with mock.patch('utils.dates_helper.local_today') as local_today:
            local_today.return_value = datetime.date(2015, 12, 1)
            stats = analytics.projections.BudgetProjections(start_date, end_date, 'account')

        row = stats.row(1)
        self.assertEqual(row['total_fee_projection'].quantize(Decimal('.01')),
                         (row['allocated_total_budget'] - row['allocated_media_budget']).quantize(Decimal('.01')))
        self.assertEqual(row['license_fee_projection'].quantize(Decimal('.01')),
                         (row['allocated_total_budget'] - row['allocated_media_budget']).quantize(Decimal('.01')))
        self.assertEqual(row['media_spend_projection'], Decimal('25000.0000'))

    def test_future_projections(self):
        self._create_batch_statements(
            dash.models.BudgetLineItem.objects.all(),
            self.today - datetime.timedelta(3),
            self.today + datetime.timedelta(3)
        )
        stats = analytics.projections.BudgetProjections(
            self.today + datetime.timedelta(1),
            self.today + datetime.timedelta(3),
            'account',
            projection_date=self.today
        )
        self.assertEqual(stats.row(1), {
            'allocated_media_budget': Decimal('1285.2941'),
            'allocated_total_budget': Decimal('1794.1176'),
            'attributed_license_fee': 0,
            'attributed_media_spend': None,
            'flat_fee': Decimal('0.0000'),
            'ideal_media_spend': None,
            'ideal_daily_media_spend': None,
            'license_fee_projection': None,
            'media_spend_projection': None,
            'pacing': None,
            'total_fee': Decimal('0.0'),
            'total_fee_projection': None
        })
        self.assertEqual(dict(stats.totals), {
            'ideal_media_spend': None,
            'ideal_daily_media_spend': None,
            'allocated_media_budget': Decimal('1285.2941'),
            'flat_fee': Decimal('0.0000'),
            'media_spend_projection': None,
            'allocated_total_budget': Decimal('1794.1176'),
            'attributed_license_fee': None,
            'total_fee_projection': None,
            'attributed_media_spend': None,
            'pacing': None,
            'total_fee': Decimal('0.0'),
            'license_fee_projection': None
        })
