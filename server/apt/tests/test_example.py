import core.models

from ..base.test_case import APTTestCase

ZEMANTA_PRODUCT_GROUP_ACCOUNT_ID = 92


class ExampleAPTTest(APTTestCase):
    def test_example_db(self):
        acc = core.models.Account.objects.get(id=ZEMANTA_PRODUCT_GROUP_ACCOUNT_ID)
        self.assertEqual("Zemanta Product Group", acc.name)
