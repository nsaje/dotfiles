from django.test import TestCase

import core.features.deals
import core.models
from utils.magic_mixer import magic_mixer

from . import helpers


class RESTAPIHelpersTest(TestCase):
    def test_get_applied_deals_dict(self):
        source = magic_mixer.blend(core.models.Source)
        ad_group = magic_mixer.blend(core.models.AdGroup)

        deal_1 = magic_mixer.blend(core.features.deals.DirectDeal, source=source)

        deal_connection_1 = magic_mixer.blend(
            core.features.deals.DirectDealConnection, adgroup=ad_group, exclusive=True, deal=deal_1
        )
        deal_connection_2 = magic_mixer.blend(core.features.deals.DirectDealConnection, exclusive=False, deal=deal_1)

        applied_deals = helpers.get_applied_deals_dict([deal_connection_1, deal_connection_2])

        self.assertEqual(
            applied_deals,
            [
                {
                    "level": deal_connection_1.level,
                    "direct_deal_connection_id": deal_connection_1.id,
                    "deal_id": deal_1.deal_id,
                    "source": deal_1.source.name,
                    "exclusive": deal_connection_1.exclusive,
                    "description": deal_1.description,
                    "is_applied": True,
                },
                {
                    "level": deal_connection_2.level,
                    "direct_deal_connection_id": deal_connection_2.id,
                    "deal_id": deal_1.deal_id,
                    "source": deal_1.source.name,
                    "exclusive": deal_connection_2.exclusive,
                    "description": deal_1.description,
                    "is_applied": False,
                },
            ],
        )

    def test_get_available_sources(self):
        released_sources = magic_mixer.cycle(2).blend(core.models.Source, deprecated=False, released=True)
        unreleased_sources = magic_mixer.cycle(2).blend(core.models.Source, deprecated=False, released=False)
        deprecated_sources = magic_mixer.cycle(2).blend(core.models.Source, deprecated=True, released=True)
        user_with_permissions = magic_mixer.blend_user(permissions=["can_see_all_available_sources"])
        user_without_permissions = magic_mixer.blend_user(permissions=[])

        # case agency has no available sources set
        agency = magic_mixer.blend(core.models.Agency, available_sources=[], allowed_sources=[])
        available_sources = helpers.get_available_sources(user_with_permissions, agency)
        self.assertTrue(released_sources + unreleased_sources == available_sources)
        self.assertTrue(deprecated_sources not in available_sources)
        available_sources = helpers.get_available_sources(user_without_permissions, agency)
        self.assertTrue(unreleased_sources not in available_sources)

        # case agency has available sources set
        agency = magic_mixer.blend(
            core.models.Agency,
            available_sources=[released_sources[0], unreleased_sources[0], deprecated_sources[0]],
            allowed_sources=[],
        )
        available_sources = helpers.get_available_sources(user_with_permissions, agency)
        self.assertEqual(set(unreleased_sources + released_sources).difference(available_sources), set())
        available_sources = helpers.get_available_sources(user_without_permissions, agency)
        self.assertTrue([released_sources[0], unreleased_sources[0], deprecated_sources[0]] == available_sources)

        # case account and its agency have sources set
        agency = magic_mixer.blend(
            core.models.Agency,
            available_sources=[released_sources[0], unreleased_sources[0], deprecated_sources[0]],
            allowed_sources=[],
        )
        account = magic_mixer.blend(
            core.models.Account,
            agency=agency,
            allowed_sources=[released_sources[1], unreleased_sources[1], deprecated_sources[1]],
        )
        available_sources = helpers.get_available_sources(user_with_permissions, agency, account=account)
        difference = {
            released_sources[0],
            unreleased_sources[0],
            released_sources[1],
            unreleased_sources[1],
        }.difference(available_sources)
        self.assertFalse(difference)
        available_sources = helpers.get_available_sources(user_with_permissions, agency, account=account)
        self.assertEqual(set(unreleased_sources + released_sources).difference(available_sources), set())
        self.assertTrue(unreleased_sources not in available_sources)

        # case create a new agency account
        agency = magic_mixer.blend(
            core.models.Agency,
            available_sources=[released_sources[0], unreleased_sources[0], deprecated_sources[0]],
            allowed_sources=[],
        )
        account = magic_mixer.blend(
            core.models.Account,
            agency=agency,
            allowed_sources=[released_sources[1], unreleased_sources[1], deprecated_sources[1]],
        )
        account.id = None
        available_sources = helpers.get_available_sources(user_with_permissions, agency, account=account)
        self.assertEqual(set(unreleased_sources + released_sources).difference(available_sources), set())
        self.assertTrue(deprecated_sources not in available_sources)

        # case create a new account
        account = magic_mixer.blend(core.models.Account, agency=None, allowed_sources=[])
        account.id = None
        available_sources = helpers.get_available_sources(user_without_permissions, None, account=account)
        difference = {*released_sources}.difference(available_sources)
        self.assertFalse(difference)
        self.assertTrue(unreleased_sources not in available_sources)
        self.assertTrue(deprecated_sources not in available_sources)
