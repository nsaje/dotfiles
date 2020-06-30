from django.test import TestCase

import core.features.deals
import core.models
import zemauth.features.entity_permission
from utils import test_helper
from utils.magic_mixer import magic_mixer
from zemauth.features.entity_permission import Permission

from .exceptions import EntityPermissionChangeNotAllowed
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

    def test_has_perm_on_all_entities(self):
        user: User = magic_mixer.blend(User)
        for permission in zemauth.features.entity_permission.Permission.get_all():
            magic_mixer.blend(
                zemauth.features.entity_permission.EntityPermission,
                user=user,
                agency=None,
                account=None,
                permission=permission,
            )
        with self.assertNumQueries(1):
            for permission in zemauth.features.entity_permission.Permission.get_all():
                self.assertTrue(user.has_perm_on_all_entities(permission))

    def test_set_entity_permissions(self):
        calling_user: zemauth.models.User = magic_mixer.blend(zemauth.models.User)
        request = type("", (), {})()
        request.user = calling_user
        agency = magic_mixer.blend(core.models.Agency)
        test_helper.add_entity_permissions(calling_user, [Permission.READ, Permission.USER], agency)
        another_agency = magic_mixer.blend(core.models.Agency)

        requested_user: zemauth.models.User = magic_mixer.blend(zemauth.models.User)

        existing_permission = zemauth.features.entity_permission.EntityPermission(
            user=requested_user, permission=Permission.READ, agency=agency
        )
        existing_permission.save()

        existing_permission_on_another_agency = zemauth.features.entity_permission.EntityPermission(
            user=requested_user, permission=Permission.READ, agency=another_agency
        )
        existing_permission_on_another_agency.save()

        # 1 existing permission on another agency + 1 existing permission on this agency
        eps = requested_user.entitypermission_set.all()
        self.assertEqual(len(eps.all()), 2)
        self.assertTrue(any(filter(lambda p: p.agency == agency and p.permission == Permission.READ, eps)))
        self.assertTrue(any(filter(lambda p: p.agency == another_agency and p.permission == Permission.READ, eps)))

        entity_permissions = [
            {"agency": agency, "permission": Permission.READ},
            {"agency": agency, "permission": Permission.BUDGET},
        ]

        requested_user.set_entity_permissions(request, None, agency, entity_permissions)

        # 1 existing permission on another agency + 2 new permissions from the request on this agency
        eps = requested_user.entitypermission_set.all()
        self.assertEqual(len(eps.all()), 3)
        self.assertTrue(any(filter(lambda p: p.agency == agency and p.permission == Permission.READ, eps)))
        self.assertTrue(any(filter(lambda p: p.agency == agency and p.permission == Permission.BUDGET, eps)))
        self.assertTrue(any(filter(lambda p: p.agency == another_agency and p.permission == Permission.READ, eps)))

    def test_set_entity_permissions_not_allowed(self):
        calling_user: zemauth.models.User = magic_mixer.blend(zemauth.models.User)
        request = type("", (), {})()
        request.user = calling_user
        agency = magic_mixer.blend(core.models.Agency)
        test_helper.add_entity_permissions(calling_user, [Permission.READ, Permission.USER], agency)
        another_agency = magic_mixer.blend(core.models.Agency)

        requested_user: zemauth.models.User = magic_mixer.blend(zemauth.models.User)

        entity_permissions = [
            {"agency": another_agency, "permission": Permission.READ},
            {"agency": another_agency, "permission": Permission.BUDGET},
        ]

        self.assertRaises(
            EntityPermissionChangeNotAllowed,
            requested_user.set_entity_permissions,
            request=request,
            account=None,
            agency=agency,
            new_entity_permissions=entity_permissions,
        )

    def test_set_entity_permissions_promote_to_internal(self):
        calling_user: zemauth.models.User = magic_mixer.blend(zemauth.models.User)
        request = type("", (), {})()
        request.user = calling_user
        test_helper.add_entity_permissions(calling_user, [Permission.READ, Permission.USER], None)
        agency = magic_mixer.blend(core.models.Agency)
        another_agency = magic_mixer.blend(core.models.Agency)

        requested_user: zemauth.models.User = magic_mixer.blend(zemauth.models.User)

        existing_permission = zemauth.features.entity_permission.EntityPermission(
            user=requested_user, permission=Permission.READ, agency=agency
        )
        existing_permission.save()

        existing_permission_on_another_agency = zemauth.features.entity_permission.EntityPermission(
            user=requested_user, permission=Permission.READ, agency=another_agency
        )
        existing_permission_on_another_agency.save()

        # 1 existing permission on another agency + 1 existing permission on this agency
        eps = requested_user.entitypermission_set.all()
        self.assertEqual(len(eps.all()), 2)
        self.assertTrue(any(filter(lambda p: p.agency == agency and p.permission == Permission.READ, eps)))
        self.assertTrue(any(filter(lambda p: p.agency == another_agency and p.permission == Permission.READ, eps)))

        entity_permissions = [{"permission": Permission.READ}, {"permission": Permission.BUDGET}]

        requested_user.set_entity_permissions(request, None, agency, entity_permissions)

        # 2 new internal permissions, all other permissions are gone
        eps = requested_user.entitypermission_set.all()
        self.assertEqual(len(eps.all()), 2)
        self.assertTrue(any(filter(lambda p: p.agency is None and p.permission == Permission.READ, eps)))
        self.assertTrue(any(filter(lambda p: p.agency is None and p.permission == Permission.BUDGET, eps)))

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
        elif permission == zemauth.features.entity_permission.Permission.BASE_COSTS_SERVICE_FEE:
            return user.has_base_costs_and_service_fee_perm_on
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
