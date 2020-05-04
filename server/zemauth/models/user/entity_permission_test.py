from django.test import TestCase

import core.features.deals
import core.models
import zemauth.features.entity_permission
from utils.magic_mixer import magic_mixer

from .model import User


class EntityPermissionMixinTestCase(TestCase):
    def setUp(self) -> None:
        self.agency = magic_mixer.blend(core.models.Agency)
        self.account = magic_mixer.blend(core.models.Account, agency=self.agency)
        self.campaign = magic_mixer.blend(core.models.Campaign, account=self.account)
        self.adgroup = magic_mixer.blend(core.models.AdGroup, campaign=self.campaign)
        self.deal = magic_mixer.blend(core.features.deals.DirectDeal, agency=self.agency)

    def test_entity_permissions(self):
        user: User = magic_mixer.blend(User)
        for permission in zemauth.features.entity_permission.Permission.get_all():
            entity_perm_function = self._get_entity_perm_function(user, permission)
            self._for_all_entities(user, entity_perm_function, permission)
            self._for_agency(user, entity_perm_function, permission)
            self._for_account(user, entity_perm_function, permission)
            self._no_access(user, entity_perm_function)

    @staticmethod
    def _get_entity_perm_function(user, permission):
        if permission == zemauth.features.entity_permission.Permission.READ:
            return user.has_read_perm_on
        elif permission == zemauth.features.entity_permission.Permission.WRITE:
            return user.has_write_perm_on
        elif permission == zemauth.features.entity_permission.Permission.USER:
            return user.has_user_perm_on
        elif permission == zemauth.features.entity_permission.Permission.BUDGET:
            return user.has_budget_perm_on
        elif permission == zemauth.features.entity_permission.Permission.BUDGET_MARGIN:
            return user.has_budget_margin_perm_on
        elif permission == zemauth.features.entity_permission.Permission.AGENCY_SPEND_MARGIN:
            return user.has_agency_spend_and_margin_perm_on
        elif permission == zemauth.features.entity_permission.Permission.MEDIA_COST_DATA_COST_LICENCE_FEE:
            return user.has_media_cost_data_cost_and_licence_fee_perm_on
        elif permission == zemauth.features.entity_permission.Permission.RESTAPI:
            return user.has_rest_api_perm_on
        else:
            raise NotImplementedError(f"Entity permission {permission} function not implemented.")

    def _for_all_entities(self, user, entity_perm_function, permission):
        user.entitypermission_set.all().delete()
        magic_mixer.blend(
            zemauth.features.entity_permission.EntityPermission,
            user=user,
            agency=None,
            account=None,
            permission=permission,
        )

        self.assertEqual(entity_perm_function(self.agency), True)
        self.assertEqual(entity_perm_function(self.account), True)
        self.assertEqual(entity_perm_function(self.campaign), True)
        self.assertEqual(entity_perm_function(self.adgroup), True)
        with self.assertRaises(TypeError):
            entity_perm_function(self.deal)

    def _for_agency(self, user, entity_perm_function, permission):
        user.entitypermission_set.all().delete()
        magic_mixer.blend(
            zemauth.features.entity_permission.EntityPermission, user=user, agency=self.agency, permission=permission
        )

        self.assertEqual(entity_perm_function(self.agency), True)
        self.assertEqual(entity_perm_function(self.account), True)
        self.assertEqual(entity_perm_function(self.campaign), True)
        self.assertEqual(entity_perm_function(self.adgroup), True)
        with self.assertRaises(TypeError):
            entity_perm_function(self.deal)

    def _for_account(self, user, entity_perm_function, permission):
        user.entitypermission_set.all().delete()
        magic_mixer.blend(
            zemauth.features.entity_permission.EntityPermission, user=user, account=self.account, permission=permission
        )

        self.assertEqual(entity_perm_function(self.agency), False)
        self.assertEqual(entity_perm_function(self.account), True)
        self.assertEqual(entity_perm_function(self.adgroup), True)
        self.assertEqual(entity_perm_function(self.campaign), True)
        with self.assertRaises(TypeError):
            entity_perm_function(self.deal)

    def _no_access(self, user, entity_perm_function):
        user.entitypermission_set.all().delete()

        self.assertEqual(entity_perm_function(self.agency), False)
        self.assertEqual(entity_perm_function(self.account), False)
        self.assertEqual(entity_perm_function(self.campaign), False)
        self.assertEqual(entity_perm_function(self.adgroup), False)
        with self.assertRaises(TypeError):
            entity_perm_function(self.deal)
