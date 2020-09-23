import core.models
import dash.constants
from utils.base_test_case import BaseTestCase
from utils.magic_mixer import magic_mixer

from . import apply_browsers_targeting


class ApplyBrowsersTargetingTestCase(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.excluded_agency = magic_mixer.blend(core.models.Agency, id=448)
        self.excluded_ad_group_one = magic_mixer.blend(
            core.models.AdGroup, campaign__account__agency=self.excluded_agency
        )

        self.excluded_account = magic_mixer.blend(core.models.Account, id=3743)
        self.excluded_ad_group_two = magic_mixer.blend(core.models.AdGroup, campaign__account=self.excluded_account)

        self.excluded_ad_group_three = magic_mixer.blend(core.models.AdGroup, id=609725)

        self.included_account = magic_mixer.blend(core.models.Account, id=5709)
        self.included_ad_group = magic_mixer.blend(core.models.AdGroup, campaign__account=self.included_account)

        self.included_ad_group_two = magic_mixer.blend(core.models.AdGroup, id=1369958)

    def test_command(self):
        command = apply_browsers_targeting.Command()
        command.handle()

        self.excluded_ad_group_one.refresh_from_db()
        self.assertEqual(
            self.excluded_ad_group_one.settings.exclusion_target_browsers, [{"family": dash.constants.BrowserFamily.IE}]
        )

        self.excluded_ad_group_two.refresh_from_db()
        self.assertEqual(
            self.excluded_ad_group_two.settings.exclusion_target_browsers,
            [
                {"family": dash.constants.BrowserFamily.IE},
                {"family": dash.constants.BrowserFamily.SAFARI},
                {"family": dash.constants.BrowserFamily.FIREFOX},
            ],
        )

        self.excluded_ad_group_three.refresh_from_db()
        self.assertEqual(
            self.excluded_ad_group_three.settings.exclusion_target_browsers,
            [{"family": dash.constants.BrowserFamily.SAFARI}],
        )

        self.included_ad_group.refresh_from_db()
        self.assertEqual(
            self.included_ad_group.settings.target_browsers,
            [{"family": dash.constants.BrowserFamily.CHROME}, {"family": dash.constants.BrowserFamily.EDGE}],
        )

        self.included_ad_group_two.refresh_from_db()
        self.assertEqual(
            self.included_ad_group_two.settings.target_browsers,
            [{"family": dash.constants.BrowserFamily.CHROME}, {"family": dash.constants.BrowserFamily.EDGE}],
        )
