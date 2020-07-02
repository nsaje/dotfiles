from secretcrypt import Secret

from ..base.test_case import APTTestCase
from ..common import Z1Client

TEST_AGENCY_ID = "781"
TEST_ACCOUNT_ID = "7180"
TEST_HIDDEN_ACCOUNT_ID = "7190"
ENT_PERM_ACCOUNT_MANAGER_CLIENT_ID = (
    Secret(
        "kms:region=us-east-1:AQICAHictPscENSYVyNw0iYdeBYCSPxW1krgRSQm+fhDfbJ85QEfjuWCgypel4KsY79PNoxgAAAAhzCBhAYJKoZIhvcNAQcGoHcwdQIBADBwBgkqhkiG9w0BBwEwHgYJYIZIAWUDBAEuMBEEDO3DTBC9xbLAqTpf4wIBEIBDhf7/Hy1G/vGcPmOtqKU4e6iPftxAPGG6KMCzflVcdgb9SmyS3PlHpIywpqqmVr+9mBuLpWVJBD76xHAlP1vLPpVl7g=="
    )
    .get()
    .decode("utf-8")
)
ENT_PERM_ACCOUNT_MANAGER_CLIENT_SECRET = (
    Secret(
        "kms:region=us-east-1:AQICAHictPscENSYVyNw0iYdeBYCSPxW1krgRSQm+fhDfbJ85QHxuE4801Yu9lRPj7MNnRd+AAAA4zCB4AYJKoZIhvcNAQcGoIHSMIHPAgEAMIHJBgkqhkiG9w0BBwEwHgYJYIZIAWUDBAEuMBEEDAiC8YT/+rW+A4OOowIBEICBm4ZlYtYYdMAmpLUmC02QSplymQXTFEyNBtb7o891+l+QcYvj78n5oLobhNIQXRf2C9pJJ75wfeunFrtBbpxhu0E9QGMsrUUDJhyJ9h1wtiQHxAD4ZaB+2tdOmKIwLTsSNgmJ2xpBOe1dO9S7etYiY2G5sNefizmo7E3GES/Hb8l5NlJiiP3l0zOCz6A9ajD5IwuCuNCMz5/8Swym"
    )
    .get()
    .decode("utf-8")
)
ENT_PERM_AGENCY_MANAGER_CLIENT_ID = (
    Secret(
        "kms:region=us-east-1:AQICAHictPscENSYVyNw0iYdeBYCSPxW1krgRSQm+fhDfbJ85QFSF5rBlRQz1vcH0+2CXaPTAAAAhzCBhAYJKoZIhvcNAQcGoHcwdQIBADBwBgkqhkiG9w0BBwEwHgYJYIZIAWUDBAEuMBEEDMMApJkujCcHnSt7SQIBEIBDV1vneg2DoVFIX56FhVfDBTY+r4l2xoGu2fxVON3BCYaxTp8HOcoLG4Syb6bxYi47YPfDJkI4qYUD/2Y42dqiVsuOig=="
    )
    .get()
    .decode("utf-8")
)
ENT_PERM_AGENCY_MANAGER_CLIENT_SECRET = (
    Secret(
        "kms:region=us-east-1:AQICAHictPscENSYVyNw0iYdeBYCSPxW1krgRSQm+fhDfbJ85QEKwL0cPauYIdxeuwYhnJDWAAAA4zCB4AYJKoZIhvcNAQcGoIHSMIHPAgEAMIHJBgkqhkiG9w0BBwEwHgYJYIZIAWUDBAEuMBEEDDyM+Pyp+LwistW7zgIBEICBm1KUzko4/uOlA/ReWn9ZbEVq/AXpNteK4RypTEUcdcV1YldjY22tdA/m8n3ArKoXaG0zbKa39i3U3BlZ1qcWGjv6f1xM0X5eRtsfK89FJzRjNRBFjpR+7yVRe5fVz9gXjEMEPcj5fMg1+w1wSGzrai92wQFIalnlu6MMNn2w5deGFIzAhMAR9vE9PTrCWlLRBpsc5KhCVe4g/2NM"
    )
    .get()
    .decode("utf-8")
)
PERM_ACCOUNT_MANAGER_CLIENT_ID = (
    Secret(
        "kms:region=us-east-1:AQICAHictPscENSYVyNw0iYdeBYCSPxW1krgRSQm+fhDfbJ85QGFD+DxelbWd77SPe+CjutvAAAAhzCBhAYJKoZIhvcNAQcGoHcwdQIBADBwBgkqhkiG9w0BBwEwHgYJYIZIAWUDBAEuMBEEDHHwxkwgTydgp5LXjwIBEIBDmaHzaS3IzwY8SRmydrDCHVb45ntC8Fmsh9HimPzbfp/wknmcILXfHQS3G7kslUtoHn6VrGqDq3UNG5F3M/bhSbZh/g=="
    )
    .get()
    .decode("utf-8")
)
PERM_ACCOUNT_MANAGER_CLIENT_SECRET = (
    Secret(
        "kms:region=us-east-1:AQICAHictPscENSYVyNw0iYdeBYCSPxW1krgRSQm+fhDfbJ85QHR2TidnuxnkwhT4Seh4SIoAAAA4zCB4AYJKoZIhvcNAQcGoIHSMIHPAgEAMIHJBgkqhkiG9w0BBwEwHgYJYIZIAWUDBAEuMBEEDDoSmSs4a/LPHWn0NAIBEICBm+q7/KnHCesg6/Mxm/Tb7uF8eUbapfYeuWFX2QrlCFi8/dn5ifJWAFkXFWXKPZ7RQdnb87EUH2sSwItygRj48twmF6OUpuVMdItAKkfPEHsZyvMdHXkzudpGBy4b35hQEwe+wywJqU3cKi12CIy81m8tuievWrR9TvEvwNxRNYBOcQhbJZCS9TCCFXnWfsfFlR1IZKQUPu8DuhHt"
    )
    .get()
    .decode("utf-8")
)
PERM_AGENCY_MANAGER_CLIENT_ID = (
    Secret(
        "kms:region=us-east-1:AQICAHictPscENSYVyNw0iYdeBYCSPxW1krgRSQm+fhDfbJ85QEBv1JPJdC1ddf0GYgrXcDYAAAAhzCBhAYJKoZIhvcNAQcGoHcwdQIBADBwBgkqhkiG9w0BBwEwHgYJYIZIAWUDBAEuMBEEDBWvdljrkRWP4xa6lwIBEIBDPUI6iRBnlWMMvVKn3hpNHxW66y+q9u/mxDWL7KQgTGbMwHtpOzL8Q6S24m4dfCLwv+p5G5l6TPPPREa7VFQux9xmUQ=="
    )
    .get()
    .decode("utf-8")
)
PERM_AGENCY_MANAGER_CLIENT_SECRET = (
    Secret(
        "kms:region=us-east-1:AQICAHictPscENSYVyNw0iYdeBYCSPxW1krgRSQm+fhDfbJ85QEkI66Y4yb2F+IxmPcvCSKcAAAA4zCB4AYJKoZIhvcNAQcGoIHSMIHPAgEAMIHJBgkqhkiG9w0BBwEwHgYJYIZIAWUDBAEuMBEEDLRRLZIPh2wwvMZCCwIBEICBm1FUOgJ1XUyiGfS1QemVp2gHw5miiL/8HqHm1O6brTFxi0bNE0AEJYhZaWsZXkP+vvKzpgYk/cOFbPPqycYIMd3pW9xzRjEpyUMZQEoQK4BZCXRDJi1EMXVdtWmoLT1oLnU02MPC77vU07pHpiiN30xIaXazw/c4AM9DN2K+HIpF7sCbaIOQQXhW1mzihTZqWuAgvyDKqxVbPTZw"
    )
    .get()
    .decode("utf-8")
)


class UserRolesAPTTestClient(Z1Client):
    BASE_URL = "https://oneapi.zemanta.com"
    AGENCIES_URL = "/rest/internal/agencies/"
    ACCOUNTS_URL = "/rest/internal/accounts/"
    ACCOUNT_URL = "/rest/internal/accounts/%s"

    def list_agencies(self):
        return self.make_api_call(self.BASE_URL + self.AGENCIES_URL, "GET").json()["data"]

    def list_accounts(self):
        return self.make_api_call(self.BASE_URL + self.ACCOUNTS_URL, "GET").json()["data"]

    def get_account(self, account_id):
        response = self.make_api_call((self.BASE_URL + self.ACCOUNT_URL) % account_id, "GET")
        if response.status_code == 404:
            return None
        else:
            return response.json()["data"]


class UserRolesAPTTest(APTTestCase):
    def setUp(self):
        self.ent_perm_account_manager_client = UserRolesAPTTestClient(
            ENT_PERM_ACCOUNT_MANAGER_CLIENT_ID, ENT_PERM_ACCOUNT_MANAGER_CLIENT_SECRET
        )
        self.ent_perm_agency_manager_client = UserRolesAPTTestClient(
            ENT_PERM_AGENCY_MANAGER_CLIENT_ID, ENT_PERM_AGENCY_MANAGER_CLIENT_SECRET
        )
        self.perm_account_manager_client = UserRolesAPTTestClient(
            PERM_ACCOUNT_MANAGER_CLIENT_ID, PERM_ACCOUNT_MANAGER_CLIENT_SECRET
        )
        self.perm_agency_manager_client = UserRolesAPTTestClient(
            PERM_AGENCY_MANAGER_CLIENT_ID, PERM_AGENCY_MANAGER_CLIENT_SECRET
        )

    def test_list_agencies(self):
        agencies_1 = self.ent_perm_account_manager_client.list_agencies()
        agencies_2 = self.ent_perm_agency_manager_client.list_agencies()
        agencies_3 = self.perm_account_manager_client.list_agencies()
        agencies_4 = self.perm_agency_manager_client.list_agencies()

        self.assertEqual(set(agency["id"] for agency in agencies_1), {TEST_AGENCY_ID})
        self.assertEqual(set(agency["id"] for agency in agencies_2), {TEST_AGENCY_ID})
        self.assertEqual(set(agency["id"] for agency in agencies_3), {TEST_AGENCY_ID})
        self.assertEqual(set(agency["id"] for agency in agencies_4), {TEST_AGENCY_ID})

    def test_list_accounts(self):
        accounts_1 = self.ent_perm_account_manager_client.list_accounts()
        accounts_2 = self.ent_perm_agency_manager_client.list_accounts()
        accounts_3 = self.perm_account_manager_client.list_accounts()
        accounts_4 = self.perm_agency_manager_client.list_accounts()

        self.assertEqual(set(account["id"] for account in accounts_1), {TEST_ACCOUNT_ID})
        self.assertEqual(set(account["id"] for account in accounts_2), {TEST_ACCOUNT_ID, TEST_HIDDEN_ACCOUNT_ID})
        self.assertEqual(set(account["id"] for account in accounts_3), {TEST_ACCOUNT_ID})
        self.assertEqual(set(account["id"] for account in accounts_4), {TEST_ACCOUNT_ID, TEST_HIDDEN_ACCOUNT_ID})

    def test_get_account(self):
        account_1 = self.ent_perm_account_manager_client.get_account(TEST_ACCOUNT_ID)
        account_2 = self.ent_perm_agency_manager_client.get_account(TEST_ACCOUNT_ID)
        account_3 = self.perm_account_manager_client.get_account(TEST_ACCOUNT_ID)
        account_4 = self.perm_agency_manager_client.get_account(TEST_ACCOUNT_ID)

        self.assertEqual(account_1["id"], TEST_ACCOUNT_ID)
        self.assertEqual(account_2["id"], TEST_ACCOUNT_ID)
        self.assertEqual(account_3["id"], TEST_ACCOUNT_ID)
        self.assertEqual(account_4["id"], TEST_ACCOUNT_ID)

        account_5 = self.ent_perm_account_manager_client.get_account(TEST_HIDDEN_ACCOUNT_ID)
        account_6 = self.ent_perm_agency_manager_client.get_account(TEST_HIDDEN_ACCOUNT_ID)
        account_7 = self.perm_account_manager_client.get_account(TEST_HIDDEN_ACCOUNT_ID)
        account_8 = self.perm_agency_manager_client.get_account(TEST_HIDDEN_ACCOUNT_ID)

        self.assertEqual(account_5, None)
        self.assertEqual(account_6["id"], TEST_HIDDEN_ACCOUNT_ID)
        self.assertEqual(account_7, None)
        self.assertEqual(account_8["id"], TEST_HIDDEN_ACCOUNT_ID)
