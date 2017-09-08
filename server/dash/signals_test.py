from django.contrib.auth import models as authmodels
from django.test import TestCase
from django.http.request import HttpRequest

from dash import models as dashmodels
from zemauth.models import User


class DashSignalsTestCase(TestCase):

    fixtures = ['test_signals.yaml']

    def test_group_account_automatically_add(self):
        perm = authmodels.Permission.objects.get(
            codename='group_account_automatically_add')
        group = authmodels.Group.objects.get(pk=1)
        group.permissions.add(perm)
        group.save()

        # This is here just to make sure that there are at least 2 groups in the database
        # because only 1 will have access to the new account.
        group2 = authmodels.Group.objects.get(pk=2)
        self.assertTrue(group2)

        request = HttpRequest()
        request.user = User(id=1)

        account = dashmodels.Account(name='New Account')
        account.save(request)

        self.assertEqual([x.pk for x in account.groups.all()], [1])

        # Make sure that existing accounts are not automatically added to the group.
        existing_account = dashmodels.Account.objects.get(pk=1)
        existing_account.name = 'existing test account 1'
        existing_account.save(request)

        self.assertEqual([x.pk for x in existing_account.groups.all()], [])
