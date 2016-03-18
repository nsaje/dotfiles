from mock import patch
from decimal import Decimal

from django.test import TestCase
from django.http.request import HttpRequest

from utils import exc
from dash import models, constants, forms
from dash import campaign_goals
from zemauth.models import User


class CampaignGoalsTestCase(TestCase):
    fixtures = ['test_models.yaml']

    def setUp(self):

        self.request = HttpRequest()
        self.request.user = User.objects.get(pk=1)
        self.campaign = models.Campaign.objects.get(pk=1)

        self.user = self.request.user

        all_goal_types = constants.CampaignGoalKPI.get_all()
        for goal_type in all_goal_types:
            models.CampaignGoal.objects.create(
                campaign=self.campaign,
                type=goal_type,
                created_by=self.user,
            )

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

    def test_create_goals_and_totals_tos(self):
        self._add_value(constants.CampaignGoalKPI.TIME_ON_SITE, 10)
        cost = 20
        row = {
            'media_cost': 20,
            'avg_tos': 20,
            'visits': 1,
        }

        expected = {
            'total_seconds': 20,
            'avg_cost_per_second': 1,
        }

        goal_totals = campaign_goals.create_goal_totals(self.campaign, row, cost)
        self.assertDictContainsSubset(expected, goal_totals)

        rows = campaign_goals.create_goals(self.campaign, [row])
        self.assertDictContainsSubset(expected, rows[0])

    def test_create_goals_and_totals_pps(self):
        self._add_value(constants.CampaignGoalKPI.PAGES_PER_SESSION, 5)
        cost = 20
        row = {
            'media_cost': 20,
            'pv_per_visit': 10,
            'visits': 1,
        }

        expected = {
            'total_pageviews': 10,
            'avg_cost_per_pageview': 2,
        }

        goal_totals = campaign_goals.create_goal_totals(self.campaign, row, cost)
        self.assertDictContainsSubset(
            expected,
            goal_totals
        )

        rows = campaign_goals.create_goals(self.campaign, [row])
        self.assertDictContainsSubset(expected, rows[0])

    def test_create_goals_and_totals_bounce_rate(self):
        self._add_value(constants.CampaignGoalKPI.MAX_BOUNCE_RATE, 0.75)
        cost = 20
        row = {
            'media_cost': 20,
            'bounce_rate': 0.75,
            'visits': 1,
        }

        expected = {
            'unbounced_visits': 0.25,
            'avg_cost_per_non_bounced_visitor': 5,
        }

        goal_totals = campaign_goals.create_goal_totals(self.campaign, row, cost)
        self.assertDictContainsSubset(
            expected,
            goal_totals
        )

        rows = campaign_goals.create_goals(self.campaign, [row])
        self.assertDictContainsSubset(expected, rows[0])

    def test_get_campaign_goal_values(self):
        self._add_value(constants.CampaignGoalKPI.MAX_BOUNCE_RATE, 0.1)
        self._add_value(constants.CampaignGoalKPI.MAX_BOUNCE_RATE, 0.5)
        self._add_value(constants.CampaignGoalKPI.MAX_BOUNCE_RATE, 0.75)

        values = campaign_goals.get_campaign_goal_values(self.campaign)
        self.assertEqual(0.75, values[0].value)

        self._add_value(constants.CampaignGoalKPI.PAGES_PER_SESSION, 5)
        self._add_value(constants.CampaignGoalKPI.TIME_ON_SITE, 60)

        values = campaign_goals.get_campaign_goal_values(
            self.campaign
        ).values_list('value', flat=True)
        self.assertItemsEqual([0.75, 5, 60], values)

    def test_get_campaign_goals(self):
        self._add_value(constants.CampaignGoalKPI.MAX_BOUNCE_RATE, 0.75)
        self._add_value(constants.CampaignGoalKPI.PAGES_PER_SESSION, 5)
        self._add_value(constants.CampaignGoalKPI.TIME_ON_SITE, 60)

        cam_goals = campaign_goals.get_campaign_goals(self.campaign)

        result = [
            {
                'name': 'time on site in seconds',
                'value': 60,
                'fields': {'total_seconds': True, 'avg_cost_per_second': True},
            },
            {
                'name': 'pages per session',
                'value': 5,
                'fields': {'total_pageviews': True, 'avg_cost_per_pageview': True},
            },
            {
                'name': 'max bounce rate %',
                'value': 0.75,
                'fields': {'unbounced_visits': True, 'avg_cost_per_non_bounced_visitor': True},
            }
        ]

        self.assertItemsEqual(result, cam_goals)
