from mock import patch
from decimal import Decimal
import datetime

from django.test import TestCase
from django.http.request import HttpRequest

from utils import exc
from dash import models, constants, forms
from dash import campaign_goals
from dash import infobox_helpers
from zemauth.models import User


class CampaignGoalsTestCase(TestCase):
    fixtures = ['test_models.yaml']

    def setUp(self):

        self.request = HttpRequest()
        self.request.user = User.objects.get(pk=1)
        self.campaign = models.Campaign.objects.get(pk=1)

        self.user = self.request.user

        all_goal_types = constants.CampaignGoalKPI.get_all()
        for i, goal_type in enumerate(all_goal_types):
            models.CampaignGoal.objects.create(
                campaign=self.campaign,
                type=goal_type,
                primary=not i,
                created_by=self.user,
            )

        cpa_goal = self._goal(constants.CampaignGoalKPI.CPA)
        conversion_goal = models.ConversionGoal.objects.create(
            campaign=self.campaign,
            type=constants.ConversionGoalType.GA,
            name='test conversion goal',
            goal_id='123',
        )
        cpa_goal.conversion_goal = conversion_goal
        cpa_goal.save()

    def _goal(self, goal_type):
        return models.CampaignGoal.objects.filter(
            type=goal_type
        ).first()

    def _add_value(self, goal_type, value):
        goal = self._goal(goal_type)
        models.CampaignGoalValue.objects.create(
            campaign_goal=goal,
            value=Decimal(value),
            created_by=self.user
        )

    def test_get_primary_campaign_goal(self):
        models.CampaignGoal.objects.all().delete()
        campaign = models.Campaign.objects.get(pk=1)
        self.assertTrue(campaign_goals.get_primary_campaign_goal(campaign) is None)

        models.CampaignGoal.objects.create(
            type=1,
            campaign=campaign,
            primary=False,
        )
        models.CampaignGoal.objects.create(
            type=2,
            campaign=campaign,
            primary=True,
        )
        self.assertEqual(campaign_goals.get_primary_campaign_goal(campaign).type, 2)

        models.CampaignGoal.objects.all().delete()
        models.CampaignGoal.objects.create(
            type=1,
            campaign_id=2,
            primary=False,
        )
        models.CampaignGoal.objects.create(
            type=2,
            campaign_id=2,
            primary=True,
        )
        self.assertTrue(campaign_goals.get_primary_campaign_goal(campaign) is None)

    def test_set_campaign_goal_primary(self):
        models.CampaignGoal.objects.all().delete()
        goal = models.CampaignGoal.objects.create(
            type=1,
            campaign_id=2,
            primary=False,
        )
        campaign_goals.set_campaign_goal_primary(self.request, self.campaign, goal.pk)
        self.assertTrue(models.CampaignGoal.objects.all()[0].primary)

        settings = self.campaign.get_current_settings()
        self.assertEqual(settings.changes_text, 'Campaign goal "time on site in seconds" set as primary')

    def test_create_campaign_goal(self):
        models.CampaignGoal.objects.all().delete()

        goal_form = forms.CampaignGoalForm({'type': 1, }, campaign_id=self.campaign.pk)
        goal = campaign_goals.create_campaign_goal(
            self.request,
            goal_form,
            self.campaign,
        )

        self.assertTrue(goal.pk)
        self.assertEqual(goal.type, 1)
        self.assertEqual(goal.campaign_id, 1)

        settings = self.campaign.get_current_settings()
        self.assertEqual(settings.changes_text, 'Added campaign goal "time on site in seconds"')

        with self.assertRaises(exc.ValidationError):
            goal_form = forms.CampaignGoalForm({}, campaign_id=self.campaign.pk)
            campaign_goals.create_campaign_goal(
                self.request,
                goal_form,
                self.campaign,
            )

    def test_delete_campaign_goal(self):
        models.CampaignGoal.objects.all().delete()
        models.ConversionGoal.objects.all().delete()

        goal = models.CampaignGoal.objects.create(
            type=1,
            primary=True,
            campaign_id=1,
        )
        models.CampaignGoalValue.objects.create(
            value=Decimal('10'),
            campaign_goal=goal,
        )

        campaign_goals.delete_campaign_goal(self.request, goal.pk, self.campaign)
        self.assertFalse(models.CampaignGoalValue.objects.all().count())
        self.assertFalse(models.CampaignGoal.objects.all().count())

        settings = self.campaign.get_current_settings()
        self.assertEqual(settings.changes_text, 'Deleted campaign goal "time on site in seconds"')

        conv_goal = models.ConversionGoal.objects.create(
            goal_id='123',
            name='123',
            type=3,
            campaign_id=1,
        )
        goal = models.CampaignGoal.objects.create(
            type=1,
            primary=True,
            campaign_id=1,
            conversion_goal=conv_goal,
        )
        models.CampaignGoalValue.objects.create(
            value=Decimal('10'),
            campaign_goal=goal,
        )

        campaign_goals.delete_campaign_goal(self.request, goal.pk, self.campaign)
        self.assertFalse(models.CampaignGoalValue.objects.all().count())
        self.assertFalse(models.CampaignGoal.objects.all().count())
        self.assertFalse(models.ConversionGoal.objects.all().count())

        settings = self.campaign.get_current_settings()
        self.assertEqual(settings.changes_text, 'Deleted conversion goal "123"')

    def test_add_campaign_goal_value(self):
        goal = models.CampaignGoal.objects.create(
            type=1,
            primary=True,
            campaign_id=1,
        )
        models.CampaignGoalValue.objects.create(
            value=Decimal('10'),
            campaign_goal=goal,
        )
        campaign_goals.add_campaign_goal_value(self.request, goal, Decimal('15'), self.campaign)

        self.assertEqual(
            [val.value for val in models.CampaignGoalValue.objects.all()],
            [Decimal('10'), Decimal('15')]
        )

        settings = self.campaign.get_current_settings()
        self.assertEqual(settings.changes_text, 'Changed campaign goal value: "15 time on site in seconds"')

    def test_get_campaign_goal_values(self):
        self._add_value(constants.CampaignGoalKPI.MAX_BOUNCE_RATE, 1)
        self._add_value(constants.CampaignGoalKPI.MAX_BOUNCE_RATE, 5)
        self._add_value(constants.CampaignGoalKPI.MAX_BOUNCE_RATE, 75)

        values = campaign_goals.get_campaign_goal_values(self.campaign)
        self.assertEqual(75, values[0].value)

        self._add_value(constants.CampaignGoalKPI.PAGES_PER_SESSION, 5)
        self._add_value(constants.CampaignGoalKPI.TIME_ON_SITE, 60)

        values = campaign_goals.get_campaign_goal_values(
            self.campaign
        ).values_list('value', flat=True)
        self.assertItemsEqual([75, 5, 60], values)

    def test_get_campaign_goals(self):
        self._add_value(constants.CampaignGoalKPI.MAX_BOUNCE_RATE, 75)
        self._add_value(constants.CampaignGoalKPI.PAGES_PER_SESSION, 5)
        self._add_value(constants.CampaignGoalKPI.TIME_ON_SITE, 60)

        self._add_value(constants.CampaignGoalKPI.CPA, 10)

        cam_goals = campaign_goals.get_campaign_goals(self.campaign, [])

        result = [
            {
                'name': 'time on site in seconds',
                'conversion': None,
                'value': 60,
                'fields': {'total_seconds': True, 'avg_cost_per_second': True},
            },
            {
                'name': 'pages per session',
                'conversion': None,
                'value': 5,
                'fields': {'total_pageviews': True, 'avg_cost_per_pageview': True},
            },
            {
                'name': 'max bounce rate %',
                'conversion': None,
                'value': 75,
                'fields': {'unbounced_visits': True, 'avg_cost_per_non_bounced_visitor': True},
            },
            {
                'name': 'Avg. cost per conversion',
                'conversion': 'test conversion goal',
                'value': 10,
                'fields': {},
            }
        ]

        self.assertItemsEqual(result, cam_goals)

    def test_get_goal_performance(self):
        start_date, end_date = datetime.date.today() - datetime.timedelta(7), datetime.date.today()

        self._add_value(constants.CampaignGoalKPI.MAX_BOUNCE_RATE, 75)
        self._add_value(constants.CampaignGoalKPI.PAGES_PER_SESSION, 5)
        self._add_value(constants.CampaignGoalKPI.TIME_ON_SITE, 60)
        self._add_value(constants.CampaignGoalKPI.CPA, 10)

        stats = {
            'conversion_goal_1': 10,
            'media_cost': 5,
            'unbounced_visits': 10,
            'total_pageviews': 10,
            'total_seconds': 10,
            'percent_new_users': 1.2,
        }
        performance = campaign_goals.get_goals_performance(self.user, self.campaign,
                                                           start_date, end_date, stats=stats)
        self.assertEqual(
            [(p[1], p[2]) for p in performance],
            [(10, Decimal('60.00000')), (0, Decimal('10.00000')), (None, None),
             (10, Decimal('5.00000')), (10, Decimal('75.00000')), (1.2, None)],
        )

    @patch('reports.api_contentads.query')
    def test_infobox(self, mock_contentads_query):
        start_date, end_date = datetime.date.today() - datetime.timedelta(7), datetime.date.today()

        self._add_value(constants.CampaignGoalKPI.MAX_BOUNCE_RATE, 75)
        self._add_value(constants.CampaignGoalKPI.PAGES_PER_SESSION, 5)
        self._add_value(constants.CampaignGoalKPI.TIME_ON_SITE, 60)
        self._add_value(constants.CampaignGoalKPI.CPA, 10)

        mock_contentads_query.return_value = {
            'unbounced_visits': 10,
            'total_pageviews': 10,
            'total_seconds': 10,
            'cpc': 0.1,
            'media_cost': 5,
            'percent_new_users': 1.2,
            'conversions': {
                'ga__123': 20.00,
            },
        }

        goals_infobox = infobox_helpers.get_campaign_goal_list(self.user, self.campaign,
                                                               start_date, end_date)
        self.assertEqual(goals_infobox, [
            {
                'section_start': True,
                'internal': True,
                'type': 'setting',
                'name': 'Campaign goals:',
                'value': '10.00 seconds on site',
                'value_class': 'primary',
                'icon': constants.Emoticon.SAD,
                'description': 'planned 60.00'
            }, {
                'section_start': False,
                'internal': False,
                'type': 'setting',
                'name': '',
                'icon': constants.Emoticon.HAPPY,
                'value': u'$0.25 CPA - test conversion goal',
                'description': 'planned $10.00'
            }, {
                'section_start': False,
                'internal': False,
                'type': 'setting',
                'name': '',
                'value': '$0.10 CPC'
            }, {
                'section_start': False,
                'internal': False,
                'type': 'setting',
                'icon': constants.Emoticon.HAPPY,
                'name': '', 'value':
                '10.00 pages per session',
                'description': 'planned 5.00'
            }, {
                'section_start': False,
                'internal': False,
                'type': 'setting',
                'name': '',
                'icon': constants.Emoticon.HAPPY,
                'value': '10.00 % bounce rate',
                'description': 'planned 75.00 %'
            }, {
                'section_start': False,
                'internal': False,
                'type': 'setting',
                'name': '',
                'value': '1.20 % new unique visitors'
            }
        ])

    def test_get_performance_value(self):
        self.assertEqual(
            campaign_goals.get_performance_value(
                constants.CampaignGoalKPI.PAGES_PER_SESSION,
                Decimal('1'),
                Decimal('1'),
            ),
            Decimal('1'),
        )
        self.assertEqual(
            campaign_goals.get_performance_value(
                constants.CampaignGoalKPI.PAGES_PER_SESSION,
                Decimal('1'),
                Decimal('1.1'),
            ),
            Decimal('0.9090909090909090909090909091'),
        )
        self.assertEqual(
            campaign_goals.get_performance_value(
                constants.CampaignGoalKPI.PAGES_PER_SESSION,
                Decimal('0.5'),
                Decimal('1'),
            ),
            Decimal('0.5'),
        )

        self.assertEqual(
            campaign_goals.get_performance_value(
                constants.CampaignGoalKPI.CPC,
                Decimal('1'),
                Decimal('1'),
            ),
            Decimal('1'),
        )
        self.assertEqual(
            campaign_goals.get_performance_value(
                constants.CampaignGoalKPI.CPC,
                Decimal('1.5'),
                Decimal('1'),
            ),
            Decimal('0.5'),
        )
        self.assertEqual(
            campaign_goals.get_performance_value(
                constants.CampaignGoalKPI.CPC,
                Decimal('0.5'),
                Decimal('1'),
            ),
            Decimal('1.5'),
        )

    def test_get_goal_performance_status(self):
        self.assertEqual(
            campaign_goals.get_goal_performance_status(
                constants.CampaignGoalKPI.PAGES_PER_SESSION,
                Decimal('1'),
                Decimal('1'),
            ),
            constants.CampaignGoalPerformance.SUPERPERFORMING,
        )
        self.assertEqual(
            campaign_goals.get_goal_performance_status(
                constants.CampaignGoalKPI.PAGES_PER_SESSION,
                Decimal('1'),
                Decimal('1.1'),
            ),
            constants.CampaignGoalPerformance.AVERAGE,
        )
        self.assertEqual(
            campaign_goals.get_goal_performance_status(
                constants.CampaignGoalKPI.PAGES_PER_SESSION,
                Decimal('0.5'),
                Decimal('1'),
            ),
            constants.CampaignGoalPerformance.UNDERPERFORMING,
        )

        self.assertEqual(
            campaign_goals.get_goal_performance_status(
                constants.CampaignGoalKPI.CPC,
                Decimal('1'),
                Decimal('1'),
            ),
            constants.CampaignGoalPerformance.SUPERPERFORMING,
        )
        self.assertEqual(
            campaign_goals.get_goal_performance_status(
                constants.CampaignGoalKPI.CPC,
                Decimal('1.5'),
                Decimal('1'),
            ),
            constants.CampaignGoalPerformance.UNDERPERFORMING,
        )
        self.assertEqual(
            campaign_goals.get_goal_performance_status(
                constants.CampaignGoalKPI.CPC,
                Decimal('1.1'),
                Decimal('1'),
            ),
            constants.CampaignGoalPerformance.AVERAGE,
        )
