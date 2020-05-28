from django.contrib.auth.models import Permission as DjangoPermission
from django.urls import reverse

import core.models
import zemauth.models
from restapi.common.views_base_test import RESTAPITestCase
from utils import test_helper
from utils.magic_mixer import magic_mixer
from zemauth.features.entity_permission import Permission


class UserViewSetTest(RESTAPITestCase):
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

    def test_get_agency_manager_1(self):
        # calling_user is agency manager and is searching by agency_id, requested user is agency manager
        calling_user, requested_user = self._setup_test()

        agency, perm1, perm2 = self._prepare_agency_manager_test_case(calling_user, requested_user, "agency_mgr")

        r = self._call_get(requested_user, agency)
        self._validate_agency_manager_response(requested_user, r, perm1, perm2)

    def test_get_agency_manager_1_with_account_id(self):
        # calling_user is agency manager and is searching by account_id, requested user is agency manager
        calling_user, requested_user = self._setup_test()

        agency, perm1, perm2 = self._prepare_agency_manager_test_case(calling_user, requested_user, "agency_mgr")
        account = self.mix_account(agency=agency)

        r = self._call_get(requested_user, agency, account)
        self._validate_agency_manager_response(requested_user, r, perm1, perm2)

    def test_get_agency_manager_2(self):
        # calling_user is internal user and is searching by agency_id, requested user is agency manager
        calling_user, requested_user = self._setup_test()

        agency, perm1, perm2 = self._prepare_agency_manager_test_case(calling_user, requested_user, "internal_usr")

        r = self._call_get(requested_user, agency)
        self._validate_agency_manager_response(requested_user, r, perm1, perm2)

    def test_get_agency_manager_2_with_account_id(self):
        # calling_user is internal user and is searching by account_id, requested user is agency manager
        calling_user, requested_user = self._setup_test()

        agency, perm1, perm2 = self._prepare_agency_manager_test_case(calling_user, requested_user, "internal_usr")
        account = self.mix_account(agency=agency)

        r = self._call_get(requested_user, agency, account)
        self._validate_agency_manager_response(requested_user, r, perm1, perm2)

    def test_get_account_manager_1(self):
        # calling_user is account manager and is searching by agency_id, requested user is account manager
        calling_user, requested_user = self._setup_test()

        account, agency, perm1, perm2 = self._prepare_account_manager_test_case(
            calling_user, requested_user, "account_mgr"
        )
        self._prepare_hidden_account_data(requested_user, agency)

        r = self._call_get(requested_user, agency)
        # this should fail because an account manager should not be searching by agency_id
        self._assertError(r, 404, "MissingDataError", "Agency does not exist")

    def test_get_account_manager_1_with_account_id(self):
        # calling_user is account manager and is searching by account_id, requested user is account manager
        calling_user, requested_user = self._setup_test()

        account, agency, perm1, perm2 = self._prepare_account_manager_test_case(
            calling_user, requested_user, "account_mgr"
        )
        self._prepare_hidden_account_data(requested_user, agency)

        r = self._call_get(requested_user, agency, account)
        self._validate_account_manager_response(perm1, perm2, r, requested_user)

    def test_get_account_manager_2(self):
        # calling_user is agency manager and is searching by agency_id, requested user is account manager
        calling_user, requested_user = self._setup_test()

        account, agency, perm1, perm2 = self._prepare_account_manager_test_case(
            calling_user, requested_user, "agency_mgr"
        )
        hidden_perm1, hidden_perm2 = self._prepare_hidden_account_data(requested_user, agency)

        r = self._call_get(requested_user, agency)
        self._validate_account_manager_response(perm1, perm2, r, requested_user, hidden_perm1, hidden_perm2)

    def test_get_account_manager_2_with_account_id(self):
        # calling_user is agency manager and is searching by account_id, requested user is account manager
        calling_user, requested_user = self._setup_test()

        account, agency, perm1, perm2 = self._prepare_account_manager_test_case(
            calling_user, requested_user, "agency_mgr"
        )
        hidden_perm1, hidden_perm2 = self._prepare_hidden_account_data(requested_user, agency)

        r = self._call_get(requested_user, agency, account)
        self._validate_account_manager_response(perm1, perm2, r, requested_user, hidden_perm1, hidden_perm2)

    def test_get_account_manager_3(self):
        # calling_user is internal user and is searching by agency_id, requested user is account manager
        calling_user, requested_user = self._setup_test()

        account, agency, perm1, perm2 = self._prepare_account_manager_test_case(
            calling_user, requested_user, "internal_usr"
        )
        hidden_perm1, hidden_perm2 = self._prepare_hidden_account_data(requested_user, agency)

        r = self._call_get(requested_user, agency)
        self._validate_account_manager_response(perm1, perm2, r, requested_user, hidden_perm1, hidden_perm2)

    def test_get_account_manager_3_with_account_id(self):
        # calling_user is internal user and is searching by account_id, requested user is account manager
        calling_user, requested_user = self._setup_test()

        account, agency, perm1, perm2 = self._prepare_account_manager_test_case(
            calling_user, requested_user, "internal_usr"
        )
        hidden_perm1, hidden_perm2 = self._prepare_hidden_account_data(requested_user, agency)

        r = self._call_get(requested_user, agency, account)
        self._validate_account_manager_response(perm1, perm2, r, requested_user, hidden_perm1, hidden_perm2)

    def _setup_test(self):
        calling_user: zemauth.models.User = self.user
        requested_user: zemauth.models.User = magic_mixer.blend(zemauth.models.User)
        return calling_user, requested_user

    def _prepare_agency_manager_test_case(self, calling_user, requested_user, caller_role):
        if caller_role == "internal_usr":
            agency = self.mix_agency()
            test_helper.add_entity_permissions(calling_user, [Permission.READ, Permission.USER], agency)
        elif caller_role == "agency_mgr":
            agency = self.mix_agency(user=calling_user, permissions=[Permission.READ, Permission.USER])

        self._prepare_hidden_data(requested_user)
        perm1 = magic_mixer.blend(zemauth.models.EntityPermission, user=requested_user, agency=agency, account=None)
        perm2 = magic_mixer.blend(zemauth.models.EntityPermission, user=requested_user, agency=agency, account=None)
        return agency, perm1, perm2

    def _prepare_hidden_data(self, requested_user):
        hidden_agency1 = self.mix_agency()
        magic_mixer.blend(zemauth.models.EntityPermission, user=requested_user, agency=hidden_agency1, account=None)
        magic_mixer.blend(zemauth.models.EntityPermission, user=requested_user, agency=hidden_agency1, account=None)
        hidden_agency2 = self.mix_agency()
        hidden_account = magic_mixer.blend(core.models.Account, agency=hidden_agency2, name="Hidden account")
        magic_mixer.blend(zemauth.models.EntityPermission, user=requested_user, agency=None, account=hidden_account)
        magic_mixer.blend(zemauth.models.EntityPermission, user=requested_user, agency=None, account=hidden_account)

    def _validate_agency_manager_response(self, requested_user, r, perm1, perm2):
        resp_json = self.assertResponseValid(r)

        self.assertEqual(resp_json["data"]["id"], str(requested_user.id))
        self.assertEqual(resp_json["data"]["email"], requested_user.email)
        self.assertEqual(resp_json["data"]["firstName"], requested_user.first_name)
        self.assertEqual(resp_json["data"]["lastName"], requested_user.last_name)
        self.assertCountEqual(
            resp_json["data"]["entityPermissions"],
            [
                {"agencyId": str(perm1.agency_id), "accountId": "", "permission": str(perm1.permission)},
                {"agencyId": str(perm2.agency_id), "accountId": "", "permission": str(perm2.permission)},
            ],
        )

    def _prepare_account_manager_test_case(self, calling_user, requested_user, caller_role):
        if caller_role == "internal_usr":
            agency = self.mix_agency()
            account = self.mix_account(agency=agency)
            test_helper.add_entity_permissions(calling_user, [Permission.READ, Permission.USER], agency)
        elif caller_role == "agency_mgr":
            agency = self.mix_agency(user=calling_user, permissions=[Permission.READ, Permission.USER])
            account = self.mix_account(agency=agency)
        elif caller_role == "account_mgr":
            agency = self.mix_agency()
            account = self.mix_account(user=calling_user, permissions=[Permission.READ, Permission.USER], agency=agency)

        self._prepare_hidden_data(requested_user)
        perm1 = magic_mixer.blend(zemauth.models.EntityPermission, user=requested_user, agency=None, account=account)
        perm2 = magic_mixer.blend(zemauth.models.EntityPermission, user=requested_user, agency=None, account=account)
        return account, agency, perm1, perm2

    def _prepare_hidden_account_data(self, requested_user, agency):
        hidden_account = self.mix_account(agency=agency)
        hidden_perm1 = magic_mixer.blend(
            zemauth.models.EntityPermission, user=requested_user, agency=None, account=hidden_account
        )
        hidden_perm2 = magic_mixer.blend(
            zemauth.models.EntityPermission, user=requested_user, agency=None, account=hidden_account
        )
        return hidden_perm1, hidden_perm2

    def _validate_account_manager_response(self, perm1, perm2, r, requested_user, hidden_perm1=None, hidden_perm2=None):
        resp_json = self.assertResponseValid(r)
        self.assertEqual(resp_json["data"]["id"], str(requested_user.id))
        self.assertEqual(resp_json["data"]["email"], requested_user.email)
        self.assertEqual(resp_json["data"]["firstName"], requested_user.first_name)
        self.assertEqual(resp_json["data"]["lastName"], requested_user.last_name)

        if hidden_perm1 is None:
            self.assertCountEqual(
                resp_json["data"]["entityPermissions"],
                [
                    {
                        "agencyId": "",
                        "accountId": str(perm1.account_id),
                        "accountName": str(perm1.account.name),
                        "permission": str(perm1.permission),
                    },
                    {
                        "agencyId": "",
                        "accountId": str(perm2.account_id),
                        "accountName": str(perm2.account.name),
                        "permission": str(perm2.permission),
                    },
                ],
            )
        else:
            self.assertCountEqual(
                resp_json["data"]["entityPermissions"],
                [
                    {
                        "agencyId": "",
                        "accountId": str(perm1.account_id),
                        "accountName": str(perm1.account.name),
                        "permission": str(perm1.permission),
                    },
                    {
                        "agencyId": "",
                        "accountId": str(perm2.account_id),
                        "accountName": str(perm2.account.name),
                        "permission": str(perm2.permission),
                    },
                    {
                        "agencyId": "",
                        "accountId": str(hidden_perm1.account_id),
                        "accountName": str(hidden_perm1.account.name),
                        "permission": str(hidden_perm1.permission),
                    },
                    {
                        "agencyId": "",
                        "accountId": str(hidden_perm2.account_id),
                        "accountName": str(hidden_perm2.account.name),
                        "permission": str(hidden_perm2.permission),
                    },
                ],
            )

    def _assertError(self, r, status_code, error_code, error_details):
        self.assertEqual(r.status_code, status_code)
        resp_json = self.assertResponseError(r, error_code)
        self.assertEqual(resp_json, {"errorCode": error_code, "details": error_details})

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
