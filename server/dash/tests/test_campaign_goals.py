from mock import patch
from decimal import Decimal

from django.test import TestCase
from django.http.request import HttpRequest

from utils import exc
from dash import models, forms
from dash import campaign_goals
from zemauth.models import User


class CampaignGoalsTestCase(TestCase):
    fixtures = ['test_models.yaml']

    def setUp(self):
        self.request = HttpRequest()
        self.request.user = User.objects.get(pk=1)
        self.campaign = models.Campaign.objects.get(pk=1)

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

    def test_create_campaign_goal(self):
        goal_form = forms.CampaignGoalForm({'type': 1, }, campaign_id=self.campaign.pk)
        goal = campaign_goals.create_campaign_goal(
            self.request,
            goal_form,
            self.campaign,
        )

        self.assertTrue(goal.pk)
        self.assertEqual(goal.type, 1)
        self.assertEqual(goal.campaign_id, 1)

        with self.assertRaises(exc.ValidationError):
            goal_form = forms.CampaignGoalForm({}, campaign_id=self.campaign.pk)
            campaign_goals.create_campaign_goal(
                self.request,
                goal_form,
                self.campaign,
            )

    def test_delete_campaign_goal(self):
        goal = models.CampaignGoal.objects.create(
            type=1,
            primary=True,
            campaign_id=1,
        )
        models.CampaignGoalValue.objects.create(
            value=Decimal('10'),
            campaign_goal=goal,
        )

        campaign_goals.delete_campaign_goal(self.request, goal.pk)
        self.assertFalse(models.CampaignGoalValue.objects.all().count())
        self.assertFalse(models.CampaignGoal.objects.all().count())

        conv_goal = models.ConversionGoal.objects.create(
            goal_id='123',
            type=2,
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

        campaign_goals.delete_campaign_goal(self.request, goal.pk)
        self.assertFalse(models.CampaignGoalValue.objects.all().count())
        self.assertFalse(models.CampaignGoal.objects.all().count())
        self.assertFalse(models.ConversionGoal.objects.all().count())

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
        campaign_goals.add_campaign_goal_value(self.request, goal.pk, Decimal('15'))

        self.assertEqual(
            [val.value for val in models.CampaignGoalValue.objects.all()],
            [Decimal('10'), Decimal('15')]
        )
