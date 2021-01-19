import mock
from django.urls import reverse
from django.utils.http import urlencode

import core.models
import zemauth.models
import zemauth.models.user.constants
from restapi.common.views_base_test_case import RESTAPITestCase
from utils import test_helper
from utils.magic_mixer import magic_mixer
from zemauth.features.entity_permission import Permission


class UserViewSetTestBase(RESTAPITestCase):
    def _setup_test_users(self):
        calling_user: zemauth.models.User = self.user
        requested_user: zemauth.models.User = magic_mixer.blend_user()
        return calling_user, requested_user

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

    def _assert_error(self, r, status_code, error_code, error_details):
        self.assertEqual(r.status_code, status_code)
        resp_json = self.assertResponseError(r, error_code)
        self.assertEqual(resp_json, {"errorCode": error_code, "details": error_details})

    def _assert_validation_error(self, r, error_text):
        try:
            self._assert_error(r, 400, "ValidationError", {"nonFieldErrors": error_text})
        except AssertionError:
            self._assert_error(r, 400, "ValidationError", error_text)

    def _expected_permission_response(self, permission):
        if permission.agency_id is not None:
            expected_response = {
                "agencyId": str(permission.agency_id),
                "accountId": None,
                "permission": str(permission.permission),
            }
        elif permission.account_id is not None:
            expected_response = {
                "agencyId": None,
                "accountId": str(permission.account_id),
                "permission": str(permission.permission),
            }
        else:
            expected_response = {"agencyId": None, "accountId": None, "permission": str(permission.permission)}

        if hasattr(permission, "assert_readonly") and permission.assert_readonly:
            expected_response["readonly"] = True

        return expected_response

    def _find_by_id(self, id, data):
        return list(filter(lambda x: str(x["id"]) == str(id), data))[0]

    def _sees_whole_agency(self, caller_role):
        return caller_role == "internal_usr" or caller_role == "agency_mgr"

    def _prepare_internal_user_test_case(self, calling_user, requested_user, caller_role):
        # output permissions:
        # [0],[1]: internal (global) permissions
        account, agency = self._prepare_callers_permissions(calling_user, caller_role)

        permissions = [None] * 2
        permissions[0] = magic_mixer.blend(
            zemauth.models.EntityPermission, user=requested_user, agency=None, account=None, permission=Permission.READ
        )
        permissions[1] = magic_mixer.blend(
            zemauth.models.EntityPermission,
            user=requested_user,
            agency=None,
            account=None,
            permission=Permission.BUDGET,
        )
        permissions[1].assert_readonly = True  # Because calling_user hasn't got BUDGET permission

        return agency, permissions

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
        permissions[1].assert_readonly = True  # Because calling_user hasn't got BUDGET permission

        permissions.extend(self._prepare_hidden_agency_data(requested_user))

        return agency, permissions

    def _prepare_account_manager_test_case(self, calling_user, requested_user, caller_role):
        # output permissions:
        # [0],[1]: permissions on the same account
        # [2],[3]: permissions on the same agency, but on a different account
        # [3] is not visible because it is a reporting permission
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
        permissions[1].assert_readonly = True  # Because calling_user hasn't got BUDGET_MARGIN permission

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
        permissions[3].assert_readonly = True  # Because calling_user hasn't got AGENCY_SPEND_MARGIN permission

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

    def _call_put(self, requested_user, put_data, agency, account=None):
        query_params = {}
        if agency is not None:
            query_params["agencyId"] = agency.id
        if account is not None:
            query_params["accountId"] = account.id

        url = u"%s?%s" % (
            reverse("restapi.user.internal:user_details", kwargs={"user_id": requested_user.id}),
            urlencode(query_params),
        )

        r = self.client.put(url, data=put_data, format="json")
        return r

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

    def _call_create(self, post_data, agency, account=None):
        query_params = {}
        if agency is not None:
            query_params["agencyId"] = agency.id
        if account is not None:
            query_params["accountId"] = account.id

        url = u"%s?%s" % (reverse("restapi.user.internal:user_list"), urlencode(query_params))

        r = self.client.post(url, data=post_data, format="json")
        return r

    def _call_delete(self, requested_user, agency, account=None):
        query_params = {}
        if agency is not None:
            query_params["agency_id"] = agency.id
        if account is not None:
            query_params["account_id"] = account.id

        url = u"%s?%s" % (
            reverse("restapi.user.internal:user_details", kwargs={"user_id": requested_user.id}),
            urlencode(query_params),
        )
        r = self.client.delete(url)
        return r

    def _call_resend_email(self, requested_user, agency, account=None):
        query_params = {}
        if agency is not None:
            query_params["agencyId"] = agency.id
        if account is not None:
            query_params["accountId"] = account.id

        url = u"%s?%s" % (
            reverse("restapi.user.internal:user_resendemail", kwargs={"user_id": requested_user.id}),
            urlencode(query_params),
        )

        r = self.client.put(url, format="json")
        return r


class UserViewSetPutTest(UserViewSetTestBase):
    def test_put_change_name(self):
        # calling_user is agency manager and is searching by agency_id, requested user is agency manager
        calling_user, requested_user = self._setup_test_users()

        agency, permissions = self._prepare_agency_manager_test_case(calling_user, requested_user, "agency_mgr")

        r = self._call_get(requested_user, agency)
        user_json = self.assertResponseValid(r)["data"]

        user_json["firstName"] = "Test"
        user_json["lastName"] = "User"

        r = self._call_put(requested_user, user_json, agency)
        self.assertResponseValid(r)

        r = self._call_get(requested_user, agency)
        user_json = self.assertResponseValid(r)["data"]

        self.assertEqual(user_json["firstName"], "Test")
        self.assertEqual(user_json["lastName"], "User")

    def test_put_change_permissions(self):
        # calling_user is agency manager and is searching by agency_id, requested user is agency manager
        calling_user, requested_user = self._setup_test_users()

        agency, permissions = self._prepare_agency_manager_test_case(calling_user, requested_user, "agency_mgr")
        test_helper.add_entity_permissions(calling_user, [Permission.BUDGET_MARGIN], agency)
        test_helper.add_entity_permissions(calling_user, [Permission.BUDGET], agency)

        r = self._call_get(requested_user, agency)
        user_json = self.assertResponseValid(r)["data"]

        user_json["entityPermissions"][0]["permission"] = Permission.READ
        user_json["entityPermissions"][1]["permission"] = Permission.USER
        user_json["entityPermissions"].append({"agencyId": agency.id, "permission": Permission.BUDGET_MARGIN})

        r = self._call_put(requested_user, user_json, agency)
        self.assertResponseValid(r)

        r = self._call_get(requested_user, agency)
        user_json = self.assertResponseValid(r)["data"]

        # After the change we need to see the same 3 permissions that we set
        self.assertCountEqual(
            user_json["entityPermissions"],
            [
                {"agencyId": str(agency.id), "accountId": None, "permission": Permission.READ},
                {"agencyId": str(agency.id), "accountId": None, "permission": Permission.USER},
                {"agencyId": str(agency.id), "accountId": None, "permission": Permission.BUDGET_MARGIN},
            ],
        )

        # But in the database, the user still also needs to have all the permissions that we don't see
        # 3 permissions that we just set + 4 permissions on other agencies = 7 permissions in total
        self.assertEqual(len(list(requested_user.entitypermission_set.all())), 7)


@mock.patch("utils.email_helper.send_official_email")
class UserViewSetCreateTest(UserViewSetTestBase):
    def test_create_on_agency(self, mock_send):
        calling_user: zemauth.models.User = self.user
        account, agency = self._prepare_callers_permissions(calling_user, "agency_mgr")
        test_helper.add_entity_permissions(calling_user, [Permission.BUDGET], agency)

        post_data = [
            {
                "email": "new.user@outbrain.com",
                "entityPermissions": [
                    {"agencyId": agency.id, "permission": Permission.READ},
                    {"agencyId": agency.id, "permission": Permission.BUDGET},
                ],
            }
        ]

        r = self._call_create(post_data, agency)
        resp_json = self.assertResponseValid(r, status_code=201, data_type=list)
        self.assertEqual(resp_json["data"][0]["email"], "new.user@outbrain.com")
        self.assertEqual(resp_json["data"][0]["firstName"], "")
        self.assertEqual(resp_json["data"][0]["lastName"], "")

        self.assertCountEqual(
            resp_json["data"][0]["entityPermissions"],
            [
                {"agencyId": str(agency.id), "accountId": None, "permission": Permission.READ},
                {"agencyId": str(agency.id), "accountId": None, "permission": Permission.BUDGET},
            ],
        )
        self.assertTrue(mock_send.called)

    def test_create_on_account(self, mock_send):
        calling_user: zemauth.models.User = self.user
        account, agency = self._prepare_callers_permissions(calling_user, "agency_mgr")

        post_data = [
            {
                "email": "new.user@outbrain.com",
                "entityPermissions": [
                    {"accountId": account.id, "permission": Permission.READ},
                    {"accountId": account.id, "permission": Permission.USER},
                ],
            }
        ]

        r = self._call_create(post_data, agency)

        resp_json = self.assertResponseValid(r, status_code=201, data_type=list)

        self.assertEqual(resp_json["data"][0]["email"], "new.user@outbrain.com")
        self.assertEqual(resp_json["data"][0]["firstName"], "")
        self.assertEqual(resp_json["data"][0]["lastName"], "")

        self.assertCountEqual(
            resp_json["data"][0]["entityPermissions"],
            [
                {"agencyId": None, "accountId": str(account.id), "permission": Permission.READ},
                {"agencyId": None, "accountId": str(account.id), "permission": Permission.USER},
            ],
        )

    def test_create_no_agency(self, mock_send):
        calling_user: zemauth.models.User = self.user
        account, agency = self._prepare_callers_permissions(calling_user, "agency_mgr")

        post_data = self._prepare_request("new.user@outbrain.com", None, None, Permission.READ)

        r = self._call_create(post_data, agency)

        self._assert_validation_error(r, "Either agency id or account id must be provided for each entity permission.")

    def test_create_internal(self, mock_send):
        calling_user: zemauth.models.User = self.user
        account, agency = self._prepare_callers_permissions(calling_user, "internal_usr")

        post_data = self._prepare_request("new.user@outbrain.com", None, None, Permission.READ)

        r = self._call_create(post_data, agency)

        resp_json = self.assertResponseValid(r, status_code=201, data_type=list)

        self.assertEqual(resp_json["data"][0]["email"], "new.user@outbrain.com")

        self.assertCountEqual(
            resp_json["data"][0]["entityPermissions"],
            [{"agencyId": None, "accountId": None, "permission": Permission.READ}],
        )

    def test_create_wrong_agency(self, mock_send):
        calling_user: zemauth.models.User = self.user
        account, agency = self._prepare_callers_permissions(calling_user, "agency_mgr")
        wrong_agency = self.mix_agency()

        post_data = self._prepare_request("new.user@outbrain.com", wrong_agency.id, None, Permission.READ)

        r = self._call_create(post_data, agency)

        self._assert_validation_error(r, "Incorrect agency ID in permission")

    def test_create_wrong_account(self, mock_send):
        calling_user: zemauth.models.User = self.user
        account, agency = self._prepare_callers_permissions(calling_user, "agency_mgr")
        wrong_account = self.mix_account(user=calling_user, permissions=[Permission.READ, Permission.USER])

        post_data = self._prepare_request("new.user@outbrain.com", None, wrong_account.id, Permission.READ)

        r = self._call_create(post_data, agency)

        self._assert_validation_error(r, "Account does not belong to the correct agency")

    def test_create_multiple(self, mock_send):
        calling_user: zemauth.models.User = self.user
        account, agency = self._prepare_callers_permissions(calling_user, "agency_mgr")

        post_data = [
            {
                "email": "new.user@outbrain.com",
                "entityPermissions": [{"permission": Permission.READ, "accountId": account.id}],
            },
            {
                "email": "new.user2@outbrain.com",
                "entityPermissions": [{"permission": Permission.READ, "accountId": account.id}],
            },
        ]

        r = self._call_create(post_data, agency)

        self.assertResponseValid(r, status_code=201, data_type=list)

    def _prepare_request(self, email, agency_id, account_id, permission):
        ep = {"permission": permission}
        if agency_id is not None:
            ep["agencyId"] = agency_id
        if account_id is not None:
            ep["accountId"] = account_id

        post_data = [{"email": email, "entityPermissions": [ep]}]
        return post_data


class UserViewSetDeleteTest(UserViewSetTestBase):
    def test_delete_account_manager_by_agency_manager_by_agency_id(self):
        calling_user: zemauth.models.User = self.user
        requested_user: zemauth.models.User = magic_mixer.blend_user()

        account, agency, permissions = self._prepare_account_manager_test_case(
            calling_user, requested_user, "agency_mgr"
        )

        self.assertCountEqual(list(requested_user.entitypermission_set.all()), permissions)

        r = self._call_delete(requested_user, agency)

        self.assertEqual(r.status_code, 204)

        self.assertCountEqual(list(requested_user.entitypermission_set.all()), permissions[4:8])

    def test_delete_account_manager_by_agency_manager_by_account_id(self):
        calling_user: zemauth.models.User = self.user
        requested_user: zemauth.models.User = magic_mixer.blend_user()

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
        requested_user: zemauth.models.User = magic_mixer.blend_user()

        account, agency, permissions = self._prepare_account_manager_test_case(
            calling_user, requested_user, "account_mgr"
        )

        self.assertCountEqual(list(requested_user.entitypermission_set.all()), permissions)

        r = self._call_delete(requested_user, agency, account)

        self.assertEqual(r.status_code, 204)

        self.assertCountEqual(list(requested_user.entitypermission_set.all()), permissions[2:8])

    def test_delete_agency_manager_by_agency_manager(self):
        calling_user: zemauth.models.User = self.user
        requested_user: zemauth.models.User = magic_mixer.blend_user()

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

        self._assert_error(r, 404, "MissingDataError", "Agency does not exist")

    def test_delete_self(self):
        # calling_user is account manager and is searching by account_id, requested user is the same as calling_user
        user = self.user
        agency = self.mix_agency()
        account = self.mix_account(
            user=user, permissions=[Permission.READ, Permission.USER, Permission.BUDGET_MARGIN], agency=agency
        )

        r = self._call_delete(user, agency, account)

        self._assert_error(r, 400, "EntityPermissionChangeNotAllowed", "User cannot delete his/her own permissions")


class UserViewSetListTest(UserViewSetTestBase):
    def test_list_no_params(self):
        r = self._call_list(None)
        self._assert_validation_error(r, "Either agency id or account id must be provided.")

    def test_list_no_agency_access(self):
        agency = self.mix_agency()

        r = self._call_list(agency)
        self._assert_error(r, 404, "MissingDataError", "Agency does not exist")

    def test_list_no_account_access(self):
        agency = self.mix_agency()
        account = self.mix_account(agency=agency)

        r = self._call_list(agency, account)
        self._assert_error(r, 404, "MissingDataError", "Account does not exist")

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
        self._assert_error(r, 404, "MissingDataError", "Agency does not exist")

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
        self._assert_validation_error(r, "You are not authorized to view internal users.")

    def test_list_by_agency_manager_with_show_internal(self):
        # calling_user is agency manager and is searching for internal users
        calling_user: zemauth.models.User = self.user

        account, agency, users, permissions = self._prepare_test_case(calling_user, "agency_mgr")

        r = self._call_list(agency, show_internal=True)
        # this should fail because an agency manager should not see internal users
        self._assert_validation_error(r, "You are not authorized to view internal users.")

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

    def _prepare_test_case(self, calling_user, caller_role):
        account, agency = self._prepare_callers_permissions(calling_user, caller_role)

        permissions = [None] * 10

        agency_mgr = magic_mixer.blend_user()
        # These 2 permissions should be visible to everybody
        permissions[0] = magic_mixer.blend(
            zemauth.models.EntityPermission, user=agency_mgr, agency=agency, account=None, permission=Permission.READ
        )
        if caller_role == "account_mgr":
            permissions[0].assert_readonly = True  # Because calling_user has a lower access level than requested_user
        permissions[1] = magic_mixer.blend(
            zemauth.models.EntityPermission, user=agency_mgr, agency=agency, account=None, permission=Permission.USER
        )
        if caller_role == "account_mgr":
            permissions[1].assert_readonly = True  # Because calling_user has a lower access level than requested_user

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

        account_mgr = magic_mixer.blend_user()
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
        permissions[5].assert_readonly = True  # Because calling_user hasn't got AGENCY_SPEND_MARGIN permission

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
        permissions[7].assert_readonly = True  # Because calling_user hasn't got BUDGET_MARGIN permission

        internal_usr = magic_mixer.blend_user()
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

        expected_entity_permissions = [self._expected_permission_response(permissions[4])]
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
    def test_get_no_params(self):
        calling_user, requested_user = self._setup_test_users()

        r = self._call_get(requested_user, None)
        self._assert_validation_error(r, "Either agency id or account id must be provided.")

    def test_get_no_agency_access(self):
        calling_user, requested_user = self._setup_test_users()

        agency = self.mix_agency()

        r = self._call_get(requested_user, agency)
        self._assert_error(r, 404, "MissingDataError", "Agency does not exist")

    def test_get_no_account_access(self):
        calling_user, requested_user = self._setup_test_users()

        agency = self.mix_agency()
        account = self.mix_account(agency=agency)

        r = self._call_get(requested_user, agency, account)
        self._assert_error(r, 404, "MissingDataError", "Account does not exist")

    def test_get_internal_user_by_agency_manager(self):
        # calling_user is agency manager and is searching by agency_id, requested user is internal user
        calling_user, requested_user = self._setup_test_users()

        agency, permissions = self._prepare_internal_user_test_case(calling_user, requested_user, "agency_mgr")

        r = self._call_get(requested_user, agency)
        self._assert_error(r, 404, "MissingDataError", "User does not exist")

    def test_get_internal_user_by_internal_user(self):
        # calling_user is internal user and is searching by agency_id, requested user is internal user
        calling_user, requested_user = self._setup_test_users()

        agency, permissions = self._prepare_internal_user_test_case(calling_user, requested_user, "internal_usr")

        r = self._call_get(requested_user, agency)
        self._validate_internal_user_response(requested_user, r, permissions)

    def test_get_agency_manager_by_agency_manager(self):
        # calling_user is agency manager and is searching by agency_id, requested user is agency manager
        calling_user, requested_user = self._setup_test_users()

        agency, permissions = self._prepare_agency_manager_test_case(calling_user, requested_user, "agency_mgr")

        r = self._call_get(requested_user, agency)
        self._validate_agency_manager_response(requested_user, r, permissions)

    def test_get_agency_manager_by_agency_manager_with_account_id(self):
        # calling_user is agency manager and is searching by account_id, requested user is agency manager
        calling_user, requested_user = self._setup_test_users()

        agency, permissions = self._prepare_agency_manager_test_case(calling_user, requested_user, "agency_mgr")
        account = self.mix_account(agency=agency)

        r = self._call_get(requested_user, agency, account)
        self._validate_agency_manager_response(requested_user, r, permissions)

    def test_get_agency_manager_by_internal_user(self):
        # calling_user is internal user and is searching by agency_id, requested user is agency manager
        calling_user, requested_user = self._setup_test_users()

        agency, permissions = self._prepare_agency_manager_test_case(calling_user, requested_user, "internal_usr")

        r = self._call_get(requested_user, agency)
        self._validate_agency_manager_response(requested_user, r, permissions)

    def test_get_agency_manager_by_internal_user_with_account_id(self):
        # calling_user is internal user and is searching by account_id, requested user is agency manager
        calling_user, requested_user = self._setup_test_users()

        agency, permissions = self._prepare_agency_manager_test_case(calling_user, requested_user, "internal_usr")
        account = self.mix_account(agency=agency)

        r = self._call_get(requested_user, agency, account)
        self._validate_agency_manager_response(requested_user, r, permissions)

    def test_get_account_manager_by_account_manager(self):
        # calling_user is account manager and is searching by agency_id, requested user is account manager
        calling_user, requested_user = self._setup_test_users()

        account, agency, permissions = self._prepare_account_manager_test_case(
            calling_user, requested_user, "account_mgr"
        )

        r = self._call_get(requested_user, agency)
        # this should fail because an account manager should not be searching by agency_id
        self._assert_error(r, 404, "MissingDataError", "Agency does not exist")

    def test_get_account_manager_by_account_manager_with_account_id(self):
        # calling_user is account manager and is searching by account_id, requested user is account manager
        calling_user, requested_user = self._setup_test_users()

        account, agency, permissions = self._prepare_account_manager_test_case(
            calling_user, requested_user, "account_mgr"
        )

        r = self._call_get(requested_user, agency, account)
        self._validate_account_manager_response(r, requested_user, permissions, "account_mgr")

    def test_get_account_manager_by_agency_manager(self):
        # calling_user is agency manager and is searching by agency_id, requested user is account manager
        calling_user, requested_user = self._setup_test_users()

        account, agency, permissions = self._prepare_account_manager_test_case(
            calling_user, requested_user, "agency_mgr"
        )

        r = self._call_get(requested_user, agency)
        self._validate_account_manager_response(r, requested_user, permissions, "agency_mgr")

    def test_get_account_manager_by_agency_manager_with_account_id(self):
        # calling_user is agency manager and is searching by account_id, requested user is account manager
        calling_user, requested_user = self._setup_test_users()

        account, agency, permissions = self._prepare_account_manager_test_case(
            calling_user, requested_user, "agency_mgr"
        )

        r = self._call_get(requested_user, agency, account)
        self._validate_account_manager_response(r, requested_user, permissions, "agency_mgr")

    def test_get_account_manager_by_internal_user(self):
        # calling_user is internal user and is searching by agency_id, requested user is account manager
        calling_user, requested_user = self._setup_test_users()

        account, agency, permissions = self._prepare_account_manager_test_case(
            calling_user, requested_user, "internal_usr"
        )

        r = self._call_get(requested_user, agency)
        self._validate_account_manager_response(r, requested_user, permissions, "internal_usr")

    def test_get_account_manager_by_internal_user_with_account_id(self):
        # calling_user is internal user and is searching by account_id, requested user is account manager
        calling_user, requested_user = self._setup_test_users()

        account, agency, permissions = self._prepare_account_manager_test_case(
            calling_user, requested_user, "internal_usr"
        )

        r = self._call_get(requested_user, agency, account)
        self._validate_account_manager_response(r, requested_user, permissions, "internal_usr")

    def _validate_internal_user_response(self, requested_user, r, permissions):
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
            expected_entity_permissions.extend([self._expected_permission_response(permissions[2])])

        self.assertCountEqual(resp_user["entityPermissions"], expected_entity_permissions)


@mock.patch("utils.email_helper.send_official_email")
class UserViewSetResendEmail(UserViewSetTestBase):
    def test_resend_email(self, mock_send):
        calling_user: zemauth.models.User = self.user
        account, agency = self._prepare_callers_permissions(calling_user, "agency_mgr")

        requested_user: zemauth.models.User = magic_mixer.blend(zemauth.models.User, email="existing.user@outbrain.com")
        test_helper.add_entity_permissions(requested_user, [Permission.READ], agency)

        r = self._call_resend_email(requested_user, agency)
        mock_send.assert_called_with(
            agency_or_user=requested_user,
            recipient_list=[requested_user.email],
            additional_recipients=[],
            subject="Welcome to Zemanta!",
            tags=["USER_NEW"],
            body=mock.ANY,
        )
        self.assertEqual(r.status_code, 200)

    def test_resend_email_no_access(self, mock_send):
        calling_user, requested_user = self._setup_test_users()
        agency = self.mix_agency(user=calling_user, permissions=[Permission.READ, Permission.USER])

        r = self._call_resend_email(requested_user, agency)
        self._assert_error(r, 404, "MissingDataError", "User does not exist")


class CurrentUserViewSetTestCase(RESTAPITestCase):
    permissions = []

    def setUp(self):
        super().setUp()
        self.user.update(status=zemauth.models.user.constants.Status.ACTIVE)
        self.agency = self.mix_agency(self.user, permissions=[Permission.READ])

    def test_get(self):
        r = self.client.get(reverse("restapi.user.internal:user_current"))
        resp_json = self.assertResponseValid(r)

        self.assertEqual(resp_json["data"]["id"], str(self.user.id))
        self.assertEqual(resp_json["data"]["email"], str(self.user.email))
        self.assertEqual(resp_json["data"]["firstName"], str(self.user.first_name))
        self.assertEqual(resp_json["data"]["lastName"], str(self.user.last_name))
        self.assertEqual(
            resp_json["data"]["status"],
            zemauth.models.user.constants.Status.get_name(zemauth.models.user.constants.Status.ACTIVE),
        )
        self.assertEqual(resp_json["data"]["name"], self.user.get_full_name())
        self.assertEqual(resp_json["data"]["permissions"], [])
        self.assertEqual(
            resp_json["data"]["entityPermissions"],
            [{"agencyId": str(self.agency.id), "accountId": None, "permission": Permission.READ}],
        )
        self.assertIsNotNone(resp_json["data"]["timezoneOffset"])
        self.assertIsNotNone(resp_json["data"]["intercomUserHash"])
        self.assertEqual(resp_json["data"]["defaultCsvSeparator"], self.agency.default_csv_separator)
        self.assertEqual(resp_json["data"]["defaultCsvDecimalSeparator"], self.agency.default_csv_decimal_separator)
