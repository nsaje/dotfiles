from django.contrib.auth.models import Permission as DjangoPermission
from django.urls import reverse
from django.utils.http import urlencode

import core.models
import zemauth.models
from restapi.common.views_base_test import RESTAPITestCase
from utils import test_helper
from utils.magic_mixer import magic_mixer
from zemauth.features.entity_permission import Permission


class UserViewSetTestBase(RESTAPITestCase):
    def _prepare_callers_permissions(self, calling_user, caller_role):
        if caller_role == "internal_usr":
            agency = self.mix_agency()
            account = self.mix_account(agency=agency)
            test_helper.add_entity_permissions(calling_user, [Permission.READ, Permission.USER], None)
        elif caller_role == "agency_mgr":
            agency = self.mix_agency(user=calling_user, permissions=[Permission.READ, Permission.USER])
            account = self.mix_account(agency=agency)
        elif caller_role == "account_mgr":
            agency = self.mix_agency()
            account = self.mix_account(user=calling_user, permissions=[Permission.READ, Permission.USER], agency=agency)
        return account, agency

    def _assertError(self, r, status_code, error_code, error_details):
        self.assertEqual(r.status_code, status_code)
        resp_json = self.assertResponseError(r, error_code)
        self.assertEqual(resp_json, {"errorCode": error_code, "details": error_details})

    def _expected_permission_response(self, permission):
        if permission.agency_id is not None:
            return {"agencyId": str(permission.agency_id), "accountId": "", "permission": str(permission.permission)}
        elif permission.account_id is not None:
            return {
                "agencyId": "",
                "accountId": str(permission.account_id),
                "accountName": str(permission.account.name),
                "permission": str(permission.permission),
            }
        else:
            return {"agencyId": "", "accountId": "", "permission": str(permission.permission)}

    def _find_by_id(self, id, data):
        return list(filter(lambda x: str(x["id"]) == str(id), data))[0]

    def _sees_whole_agency(self, caller_role):
        return caller_role == "internal_usr" or caller_role == "agency_mgr"

    def _prepare_agency_manager_test_case(self, calling_user, requested_user, caller_role):
        # output permissions:
        # [0],[1]: permissions on the same agency
        # [2],[3]: permissions on a different agency
        # [4],[5]: permissions on an account in a different agency
        account, agency = self._prepare_callers_permissions(calling_user, caller_role)

        permissions = [None] * 2
        permissions[0] = magic_mixer.blend(
            zemauth.models.EntityPermission,
            user=requested_user,
            agency=agency,
            account=None,
            permission=Permission.READ,
        )
        permissions[1] = magic_mixer.blend(
            zemauth.models.EntityPermission,
            user=requested_user,
            agency=agency,
            account=None,
            permission=Permission.BUDGET,
        )

        permissions.extend(self._prepare_hidden_agency_data(requested_user))

        return agency, permissions

    def _prepare_account_manager_test_case(self, calling_user, requested_user, caller_role):
        # output permissions:
        # [0],[1]: permissions on the same account
        # [2],[3]: permissions on the same agency, but on a different account
        # [4],[5]: permissions on a different agency
        # [6],[7]: permissions on an account in a different agency
        account, agency = self._prepare_callers_permissions(calling_user, caller_role)

        permissions = [None] * 4

        permissions[0] = magic_mixer.blend(
            zemauth.models.EntityPermission,
            user=requested_user,
            agency=None,
            account=account,
            permission=Permission.READ,
        )
        permissions[1] = magic_mixer.blend(
            zemauth.models.EntityPermission,
            user=requested_user,
            agency=None,
            account=account,
            permission=Permission.BUDGET_MARGIN,
        )

        hidden_account = self.mix_account(agency=agency)
        permissions[2] = magic_mixer.blend(
            zemauth.models.EntityPermission,
            user=requested_user,
            agency=None,
            account=hidden_account,
            permission=Permission.READ,
        )
        permissions[3] = magic_mixer.blend(
            zemauth.models.EntityPermission,
            user=requested_user,
            agency=None,
            account=hidden_account,
            permission=Permission.AGENCY_SPEND_MARGIN,
        )

        permissions.extend(self._prepare_hidden_agency_data(requested_user))

        return account, agency, permissions

    def _prepare_hidden_agency_data(self, requested_user):
        permissions = [None] * 4

        hidden_agency1 = self.mix_agency()
        permissions[0] = magic_mixer.blend(
            zemauth.models.EntityPermission,
            user=requested_user,
            agency=hidden_agency1,
            account=None,
            permission=Permission.READ,
        )
        permissions[1] = magic_mixer.blend(
            zemauth.models.EntityPermission,
            user=requested_user,
            agency=hidden_agency1,
            account=None,
            permission=Permission.USER,
        )
        hidden_agency2 = self.mix_agency()
        hidden_account = magic_mixer.blend(core.models.Account, agency=hidden_agency2, name="Hidden account")
        permissions[2] = magic_mixer.blend(
            zemauth.models.EntityPermission,
            user=requested_user,
            agency=None,
            account=hidden_account,
            permission=Permission.READ,
        )
        permissions[3] = magic_mixer.blend(
            zemauth.models.EntityPermission,
            user=requested_user,
            agency=None,
            account=hidden_account,
            permission=Permission.AGENCY_SPEND_MARGIN,
        )

        return permissions


class UserViewSetDeleteTest(UserViewSetTestBase):
    def test_delete_account_manager_by_agency_manager_by_agency_id(self):
        calling_user: zemauth.models.User = self.user
        requested_user: zemauth.models.User = magic_mixer.blend(zemauth.models.User)

        account, agency, permissions = self._prepare_account_manager_test_case(
            calling_user, requested_user, "agency_mgr"
        )

        self.assertCountEqual(list(requested_user.entitypermission_set.all()), permissions)

        r = self._call_delete(requested_user, agency)

        self.assertEqual(r.status_code, 204)

        self.assertCountEqual(list(requested_user.entitypermission_set.all()), permissions[4:8])

    def test_delete_account_manager_by_agency_manager_by_account_id(self):
        calling_user: zemauth.models.User = self.user
        requested_user: zemauth.models.User = magic_mixer.blend(zemauth.models.User)

        account, agency, permissions = self._prepare_account_manager_test_case(
            calling_user, requested_user, "agency_mgr"
        )

        self.assertCountEqual(list(requested_user.entitypermission_set.all()), permissions)

        r = self._call_delete(requested_user, agency, account)

        self.assertEqual(r.status_code, 204)

        # IMPORTANT: even though we retrieved this user by account ID, the delete operation must delete permissions on all accounts of this agency, because the calling user is an agency manager
        self.assertCountEqual(list(requested_user.entitypermission_set.all()), permissions[4:8])

    def test_delete_account_manager_by_account_manager(self):
        calling_user: zemauth.models.User = self.user
        requested_user: zemauth.models.User = magic_mixer.blend(zemauth.models.User)

        account, agency, permissions = self._prepare_account_manager_test_case(
            calling_user, requested_user, "account_mgr"
        )

        self.assertCountEqual(list(requested_user.entitypermission_set.all()), permissions)

        r = self._call_delete(requested_user, agency, account)

        self.assertEqual(r.status_code, 204)

        self.assertCountEqual(list(requested_user.entitypermission_set.all()), permissions[2:8])

    def test_delete_agency_manager_by_agency_manager(self):
        calling_user: zemauth.models.User = self.user
        requested_user: zemauth.models.User = magic_mixer.blend(zemauth.models.User)

        agency, permissions = self._prepare_agency_manager_test_case(calling_user, requested_user, "agency_mgr")

        self.assertCountEqual(list(requested_user.entitypermission_set.all()), permissions)

        r = self._call_delete(requested_user, agency)

        self.assertEqual(r.status_code, 204)

        self.assertCountEqual(list(requested_user.entitypermission_set.all()), permissions[2:6])

    def test_delete_agency_manager_by_account_manager(self):
        calling_user: zemauth.models.User = self.user
        requested_user: zemauth.models.User = magic_mixer.blend(zemauth.models.User)

        agency, permissions = self._prepare_agency_manager_test_case(calling_user, requested_user, "account_mgr")

        self.assertCountEqual(list(requested_user.entitypermission_set.all()), permissions)

        r = self._call_delete(requested_user, agency)

        self._assertError(r, 404, "MissingDataError", "Agency does not exist")

    def _call_delete(self, requested_user, agency, account=None):
        query_params = {}
        if agency is not None:
            query_params["agency_id"] = agency.id
        if account is not None:
            query_params["account_id"] = account.id

        """r = self.client.delete(
            reverse("restapi.user.internal:user_details", kwargs={"user_id": requested_user.id}), query_params
        )"""
        r = self.client.delete(
            u"%s?%s"
            % (
                reverse("restapi.user.internal:user_details", kwargs={"user_id": requested_user.id}),
                urlencode(query_params),
            )
        )
        return r


class UserViewSetListTest(UserViewSetTestBase):
    def test_list_no_permission(self):
        calling_user: zemauth.models.User = self.user
        calling_user.user_permissions.remove(
            DjangoPermission.objects.get(user=calling_user, codename="fea_use_entity_permission")
        )

        agency = self.mix_agency(user=calling_user, permissions=[Permission.READ, Permission.USER])

        r = self._call_list(agency)
        self._assertError(r, 403, "PermissionDenied", "You do not have permission to perform this action.")

    def test_list_no_params(self):
        r = self._call_list(None)
        self._assertError(
            r, 400, "ValidationError", {"nonFieldErrors": "Either agency id or account id must be provided."}
        )

    def test_list_no_agency_access(self):
        agency = self.mix_agency()

        r = self._call_list(agency)
        self._assertError(r, 404, "MissingDataError", "Agency does not exist")

    def test_list_no_account_access(self):
        agency = self.mix_agency()
        account = self.mix_account(agency=agency)

        r = self._call_list(agency, account)
        self._assertError(r, 404, "MissingDataError", "Account does not exist")

    def test_list_keyword(self):
        # calling_user is agency manager and is searching by agency_id and keyword
        calling_user: zemauth.models.User = self.user

        account, agency, users, permissions = self._prepare_test_case(calling_user, "agency_mgr")

        user2 = magic_mixer.blend(zemauth.models.User, first_name="test", last_name="test", email="test.test@test.com")
        magic_mixer.blend(
            zemauth.models.EntityPermission, user=user2, agency=agency, account=None, permission=Permission.READ
        )
        user3 = magic_mixer.blend(
            zemauth.models.User, first_name="test", last_name="test", email="kdfjzhgks.test@test.com"
        )
        magic_mixer.blend(
            zemauth.models.EntityPermission, user=user3, agency=agency, account=None, permission=Permission.READ
        )
        user4 = magic_mixer.blend(
            zemauth.models.User, first_name="test", last_name="Kdfjzhgks", email="test4.test@test.com"
        )
        magic_mixer.blend(
            zemauth.models.EntityPermission, user=user4, agency=agency, account=None, permission=Permission.READ
        )
        user5 = magic_mixer.blend(
            zemauth.models.User, first_name="Kdfjzhgks", last_name="test", email="test5.test@test.com"
        )
        magic_mixer.blend(
            zemauth.models.EntityPermission, user=user5, agency=agency, account=None, permission=Permission.READ
        )

        r = self._call_list(agency, keyword="fjzhg")

        response = self.assertResponseValid(r, data_type=list, status_code=200)

        response_user_ids = map(lambda x: x["id"], response["data"])
        expected_user_ids = map(lambda x: str(x.id), [user3, user4, user5])

        self.assertCountEqual(response_user_ids, expected_user_ids)

    def test_list_by_account_manager(self):
        # calling_user is account manager and is searching by agency_id
        calling_user: zemauth.models.User = self.user

        account, agency, users, permissions = self._prepare_test_case(calling_user, "account_mgr")

        r = self._call_list(agency)
        # this should fail because an account manager should not be searching by agency_id
        self._assertError(r, 404, "MissingDataError", "Agency does not exist")

    def test_list_by_account_manager_with_account_id(self):
        # calling_user is account manager and is searching by account_id
        calling_user: zemauth.models.User = self.user

        account, agency, users, permissions = self._prepare_test_case(calling_user, "account_mgr")

        r = self._call_list(agency, account)
        self._validate_response(r, users, permissions, "account_mgr")

    def test_list_by_agency_manager(self):
        # calling_user is agency manager and is searching by agency_id
        calling_user: zemauth.models.User = self.user

        account, agency, users, permissions = self._prepare_test_case(calling_user, "agency_mgr")

        r = self._call_list(agency)
        self._validate_response(r, users, permissions, "agency_mgr")

    def test_list_by_agency_manager_with_account_id(self):
        # calling_user is agency manager and is searching by account_id
        calling_user: zemauth.models.User = self.user

        account, agency, users, permissions = self._prepare_test_case(calling_user, "agency_mgr")

        r = self._call_list(agency, account)
        self._validate_response(r, users, permissions, "agency_mgr")

    def test_list_by_account_manager_with_account_id_and_show_internal(self):
        # calling_user is account manager and is searching for internal users by account_id
        calling_user: zemauth.models.User = self.user

        account, agency, users, permissions = self._prepare_test_case(calling_user, "account_mgr")

        r = self._call_list(agency, account, show_internal=True)
        # this should fail because an account manager should not see internal users
        self._assertError(
            r, 400, "ValidationError", {"nonFieldErrors": "You are not authorized to view internal users."}
        )

    def test_list_by_agency_manager_with_show_internal(self):
        # calling_user is agency manager and is searching for internal users
        calling_user: zemauth.models.User = self.user

        account, agency, users, permissions = self._prepare_test_case(calling_user, "agency_mgr")

        r = self._call_list(agency, show_internal=True)
        # this should fail because an agency manager should not see internal users
        self._assertError(
            r, 400, "ValidationError", {"nonFieldErrors": "You are not authorized to view internal users."}
        )

    def test_list_by_internal_user(self):
        # calling_user is internal user and is searching by agency_id
        calling_user: zemauth.models.User = self.user

        account, agency, users, permissions = self._prepare_test_case(calling_user, "internal_usr")

        r = self._call_list(agency)
        self._validate_response(r, users, permissions, "internal_usr")

    def test_list_by_internal_user_with_account_id(self):
        # calling_user is internal user and is searching by account_id
        calling_user: zemauth.models.User = self.user

        account, agency, users, permissions = self._prepare_test_case(calling_user, "internal_usr")

        r = self._call_list(agency, account)
        self._validate_response(r, users, permissions, "internal_usr")

    def test_list_by_internal_user_with_show_internal(self):
        # calling_user is internal user and is searching for internal users by agency_id
        calling_user: zemauth.models.User = self.user

        account, agency, users, permissions = self._prepare_test_case(calling_user, "internal_usr")

        r = self._call_list(agency, limit=1000, show_internal=True)
        self._validate_response(r, users, permissions, "internal_usr", show_internal=True)

    def test_list_by_internal_user_with_account_id_and_show_internal(self):
        # calling_user is internal user and is searching for internal users by account_id
        calling_user: zemauth.models.User = self.user

        account, agency, users, permissions = self._prepare_test_case(calling_user, "internal_usr")

        r = self._call_list(agency, account, limit=1000, show_internal=True)
        self._validate_response(r, users, permissions, "internal_usr", show_internal=True)

    def _call_list(self, agency, account=None, offset=0, limit=10, show_internal=None, keyword=None):
        query_params = {}
        if agency is not None:
            query_params["agencyId"] = agency.id
        if account is not None:
            query_params["accountId"] = account.id
        if offset is not None:
            query_params["offset"] = offset
        if limit is not None:
            query_params["limit"] = limit
        if show_internal is not None:
            query_params["show_internal"] = show_internal
        if keyword is not None:
            query_params["keyword"] = keyword

        r = self.client.get(reverse("restapi.user.internal:user_list"), query_params)
        return r

    def _prepare_test_case(self, calling_user, caller_role):
        account, agency = self._prepare_callers_permissions(calling_user, caller_role)

        permissions = [None] * 10

        agency_mgr = magic_mixer.blend(zemauth.models.User)
        # These 2 permissions should be visible to everybody
        permissions[0] = magic_mixer.blend(
            zemauth.models.EntityPermission, user=agency_mgr, agency=agency, account=None, permission=Permission.READ
        )
        permissions[1] = magic_mixer.blend(
            zemauth.models.EntityPermission, user=agency_mgr, agency=agency, account=None, permission=Permission.USER
        )

        another_agency = self.mix_agency()
        # These 2 permissions should not be visible to anybody, because they are on a different agency
        permissions[2] = magic_mixer.blend(
            zemauth.models.EntityPermission,
            user=agency_mgr,
            agency=another_agency,
            account=None,
            permission=Permission.READ,
        )
        permissions[3] = magic_mixer.blend(
            zemauth.models.EntityPermission,
            user=agency_mgr,
            agency=another_agency,
            account=None,
            permission=Permission.BUDGET,
        )

        account_mgr = magic_mixer.blend(zemauth.models.User)
        # These 2 permissions should be visible to everybody
        permissions[4] = magic_mixer.blend(
            zemauth.models.EntityPermission, user=account_mgr, agency=None, account=account, permission=Permission.READ
        )
        permissions[5] = magic_mixer.blend(
            zemauth.models.EntityPermission,
            user=account_mgr,
            agency=None,
            account=account,
            permission=Permission.AGENCY_SPEND_MARGIN,
        )

        another_account = self.mix_account(agency=agency)
        # These 2 permissions should be visible to internal users and agency managers, but not to the account manager who has no access to this account
        permissions[6] = magic_mixer.blend(
            zemauth.models.EntityPermission,
            user=account_mgr,
            agency=None,
            account=another_account,
            permission=Permission.READ,
        )
        permissions[7] = magic_mixer.blend(
            zemauth.models.EntityPermission,
            user=account_mgr,
            agency=None,
            account=another_account,
            permission=Permission.BUDGET_MARGIN,
        )

        internal_usr = magic_mixer.blend(zemauth.models.User)
        # These 2 permissions should only be visible to internal users IF the show_internal query parameter is set to True
        permissions[8] = magic_mixer.blend(
            zemauth.models.EntityPermission, user=internal_usr, agency=None, account=None, permission=Permission.READ
        )
        permissions[9] = magic_mixer.blend(
            zemauth.models.EntityPermission, user=internal_usr, agency=None, account=None, permission=Permission.USER
        )

        users = [agency_mgr, account_mgr, internal_usr]

        return account, agency, users, permissions

    def _validate_response(self, r, users, permissions, caller_role, show_internal=None):
        response = self.assertResponseValid(r, data_type=list, status_code=200)

        agency_mgr = users[0]
        agency_mgr_response = self._find_by_id(agency_mgr.id, response["data"])

        self.assertEqual(agency_mgr_response["id"], str(agency_mgr.id))
        self.assertEqual(agency_mgr_response["email"], agency_mgr.email)
        self.assertEqual(agency_mgr_response["firstName"], agency_mgr.first_name)
        self.assertEqual(agency_mgr_response["lastName"], agency_mgr.last_name)

        self.assertCountEqual(
            agency_mgr_response["entityPermissions"],
            [self._expected_permission_response(permissions[0]), self._expected_permission_response(permissions[1])],
        )

        account_mgr = users[1]
        account_mgr_response = self._find_by_id(account_mgr.id, response["data"])
        self.assertEqual(account_mgr_response["id"], str(account_mgr.id))
        self.assertEqual(account_mgr_response["email"], account_mgr.email)
        self.assertEqual(account_mgr_response["firstName"], account_mgr.first_name)
        self.assertEqual(account_mgr_response["lastName"], account_mgr.last_name)

        expected_entity_permissions = [
            self._expected_permission_response(permissions[4]),
            self._expected_permission_response(permissions[5]),
        ]
        if self._sees_whole_agency(caller_role):
            expected_entity_permissions.extend(
                [self._expected_permission_response(permissions[6]), self._expected_permission_response(permissions[7])]
            )

        self.assertCountEqual(account_mgr_response["entityPermissions"], expected_entity_permissions)

        if caller_role == "internal_usr" and show_internal:
            internal_usr = users[2]
            internal_usr_response = self._find_by_id(internal_usr.id, response["data"])

            expected_entity_permissions = [
                self._expected_permission_response(permissions[8]),
                self._expected_permission_response(permissions[9]),
            ]
            self.assertCountEqual(internal_usr_response["entityPermissions"], expected_entity_permissions)


class UserViewSetGetTest(UserViewSetTestBase):
    def test_get_no_permission(self):
        calling_user, requested_user = self._setup_test()
        calling_user.user_permissions.remove(
            DjangoPermission.objects.get(user=calling_user, codename="fea_use_entity_permission")
        )

        agency = self.mix_agency(user=calling_user, permissions=[Permission.READ, Permission.USER])

        r = self._call_get(requested_user, agency)
        self._assertError(r, 403, "PermissionDenied", "You do not have permission to perform this action.")

    def test_get_no_params(self):
        calling_user, requested_user = self._setup_test()

        r = self._call_get(requested_user, None)
        self._assertError(
            r, 400, "ValidationError", {"nonFieldErrors": "Either agency id or account id must be provided."}
        )

    def test_get_no_agency_access(self):
        calling_user, requested_user = self._setup_test()

        agency = self.mix_agency()

        r = self._call_get(requested_user, agency)
        self._assertError(r, 404, "MissingDataError", "Agency does not exist")

    def test_get_no_account_access(self):
        calling_user, requested_user = self._setup_test()

        agency = self.mix_agency()
        account = self.mix_account(agency=agency)

        r = self._call_get(requested_user, agency, account)
        self._assertError(r, 404, "MissingDataError", "Account does not exist")

    def test_get_agency_manager_by_agency_manager(self):
        # calling_user is agency manager and is searching by agency_id, requested user is agency manager
        calling_user, requested_user = self._setup_test()

        agency, permissions = self._prepare_agency_manager_test_case(calling_user, requested_user, "agency_mgr")

        r = self._call_get(requested_user, agency)
        self._validate_agency_manager_response(requested_user, r, permissions)

    def test_get_agency_manager_by_agency_manager_with_account_id(self):
        # calling_user is agency manager and is searching by account_id, requested user is agency manager
        calling_user, requested_user = self._setup_test()

        agency, permissions = self._prepare_agency_manager_test_case(calling_user, requested_user, "agency_mgr")
        account = self.mix_account(agency=agency)

        r = self._call_get(requested_user, agency, account)
        self._validate_agency_manager_response(requested_user, r, permissions)

    def test_get_agency_manager_by_internal_user(self):
        # calling_user is internal user and is searching by agency_id, requested user is agency manager
        calling_user, requested_user = self._setup_test()

        agency, permissions = self._prepare_agency_manager_test_case(calling_user, requested_user, "internal_usr")

        r = self._call_get(requested_user, agency)
        self._validate_agency_manager_response(requested_user, r, permissions)

    def test_get_agency_manager_by_internal_user_with_account_id(self):
        # calling_user is internal user and is searching by account_id, requested user is agency manager
        calling_user, requested_user = self._setup_test()

        agency, permissions = self._prepare_agency_manager_test_case(calling_user, requested_user, "internal_usr")
        account = self.mix_account(agency=agency)

        r = self._call_get(requested_user, agency, account)
        self._validate_agency_manager_response(requested_user, r, permissions)

    def test_get_account_manager_by_account_manager(self):
        # calling_user is account manager and is searching by agency_id, requested user is account manager
        calling_user, requested_user = self._setup_test()

        account, agency, permissions = self._prepare_account_manager_test_case(
            calling_user, requested_user, "account_mgr"
        )

        r = self._call_get(requested_user, agency)
        # this should fail because an account manager should not be searching by agency_id
        self._assertError(r, 404, "MissingDataError", "Agency does not exist")

    def test_get_account_manager_by_account_manager_with_account_id(self):
        # calling_user is account manager and is searching by account_id, requested user is account manager
        calling_user, requested_user = self._setup_test()

        account, agency, permissions = self._prepare_account_manager_test_case(
            calling_user, requested_user, "account_mgr"
        )

        r = self._call_get(requested_user, agency, account)
        self._validate_account_manager_response(r, requested_user, permissions, "account_mgr")

    def test_get_account_manager_by_agency_manager(self):
        # calling_user is agency manager and is searching by agency_id, requested user is account manager
        calling_user, requested_user = self._setup_test()

        account, agency, permissions = self._prepare_account_manager_test_case(
            calling_user, requested_user, "agency_mgr"
        )

        r = self._call_get(requested_user, agency)
        self._validate_account_manager_response(r, requested_user, permissions, "agency_mgr")

    def test_get_account_manager_by_agency_manager_with_account_id(self):
        # calling_user is agency manager and is searching by account_id, requested user is account manager
        calling_user, requested_user = self._setup_test()

        account, agency, permissions = self._prepare_account_manager_test_case(
            calling_user, requested_user, "agency_mgr"
        )

        r = self._call_get(requested_user, agency, account)
        self._validate_account_manager_response(r, requested_user, permissions, "agency_mgr")

    def test_get_account_manager_by_internal_user(self):
        # calling_user is internal user and is searching by agency_id, requested user is account manager
        calling_user, requested_user = self._setup_test()

        account, agency, permissions = self._prepare_account_manager_test_case(
            calling_user, requested_user, "internal_usr"
        )

        r = self._call_get(requested_user, agency)
        self._validate_account_manager_response(r, requested_user, permissions, "internal_usr")

    def test_get_account_manager_by_internal_user_with_account_id(self):
        # calling_user is internal user and is searching by account_id, requested user is account manager
        calling_user, requested_user = self._setup_test()

        account, agency, permissions = self._prepare_account_manager_test_case(
            calling_user, requested_user, "internal_usr"
        )

        r = self._call_get(requested_user, agency, account)
        self._validate_account_manager_response(r, requested_user, permissions, "internal_usr")

    def _setup_test(self):
        calling_user: zemauth.models.User = self.user
        requested_user: zemauth.models.User = magic_mixer.blend(zemauth.models.User)
        return calling_user, requested_user

    def _validate_agency_manager_response(self, requested_user, r, permissions):
        resp_json = self.assertResponseValid(r)

        resp_user = resp_json["data"]
        self.assertEqual(resp_user["id"], str(requested_user.id))
        self.assertEqual(resp_user["email"], requested_user.email)
        self.assertEqual(resp_user["firstName"], requested_user.first_name)
        self.assertEqual(resp_user["lastName"], requested_user.last_name)
        self.assertCountEqual(
            resp_user["entityPermissions"],
            [self._expected_permission_response(permissions[0]), self._expected_permission_response(permissions[1])],
        )

    def _validate_account_manager_response(self, r, requested_user, permissions, caller_role):
        resp_json = self.assertResponseValid(r)

        resp_user = resp_json["data"]
        self.assertEqual(resp_user["id"], str(requested_user.id))
        self.assertEqual(resp_user["email"], requested_user.email)
        self.assertEqual(resp_user["firstName"], requested_user.first_name)
        self.assertEqual(resp_user["lastName"], requested_user.last_name)

        expected_entity_permissions = [
            self._expected_permission_response(permissions[0]),
            self._expected_permission_response(permissions[1]),
        ]
        if self._sees_whole_agency(caller_role):
            expected_entity_permissions.extend(
                [self._expected_permission_response(permissions[2]), self._expected_permission_response(permissions[3])]
            )

        self.assertCountEqual(resp_user["entityPermissions"], expected_entity_permissions)

    def _call_get(self, requested_user, agency, account=None):
        query_params = {}
        if agency is not None:
            query_params["agencyId"] = agency.id
        if account is not None:
            query_params["accountId"] = account.id

        r = self.client.get(
            reverse("restapi.user.internal:user_details", kwargs={"user_id": requested_user.id}), query_params
        )
        return r
