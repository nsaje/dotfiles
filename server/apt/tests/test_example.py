import core.models

from ..base.test_case import APTTestCase


class ExampleAPTTest(APTTestCase):
    def test_example_db(self):
        acc = core.models.Account.objects.get(id=92)
        self.assertEqual("Zemanta Product Group", acc.name)
