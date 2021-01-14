import core.models
import dash.constants
from utils.base_test_case import BaseTestCase
from utils.magic_mixer import magic_mixer

from . import apply_js_tracking


class ApplyJsTrackingTestCase(BaseTestCase):
    def setUp(self):
        super().setUp()
        existing_trackers = [
            {
                "event_type": dash.constants.TrackerEventType.IMPRESSION,
                "method": dash.constants.TrackerMethod.JS,
                "url": "https://t.test.com/tracker.js",
                "fallback_url": None,
                "tracker_optional": False,
                "supported_privacy_frameworks": [],
            }
        ]

        self.contentad = magic_mixer.blend(core.models.ContentAd, id=3316419, trackers=existing_trackers)

        self.adgroup = magic_mixer.blend(core.models.AdGroup, id=413741)
        magic_mixer.cycle(3).blend(core.models.ContentAd, ad_group=self.adgroup, trackers=existing_trackers)

        self.account = magic_mixer.blend(core.models.Account, id=6778)
        magic_mixer.cycle(3).blend(
            core.models.ContentAd, ad_group__campaign__account=self.account, trackers=existing_trackers
        )

        self.agency = magic_mixer.blend(core.models.Agency, id=206)
        magic_mixer.cycle(3).blend(
            core.models.ContentAd, ad_group__campaign__account__agency=self.agency, trackers=existing_trackers
        )

    def test_command(self):
        self.maxDiff = None
        command = apply_js_tracking.Command()
        command._apply_bidder_hacks()

        self.contentad.refresh_from_db()
        self.assertEqual(
            self.contentad.trackers,
            [
                {
                    "event_type": dash.constants.TrackerEventType.IMPRESSION,
                    "method": dash.constants.TrackerMethod.JS,
                    "url": "https://t.test.com/tracker.js",
                    "fallback_url": None,
                    "tracker_optional": False,
                    "supported_privacy_frameworks": [],
                },
                {
                    "event_type": dash.constants.TrackerEventType.IMPRESSION,
                    "method": dash.constants.TrackerMethod.JS,
                    "url": "https://pixel.adsafeprotected.com/rjss/st/166348/27091079/skeleton.js",
                    "fallback_url": "https://pixel.adsafeprotected.com/rfw/st/166348/27091078/skeleton.gif",
                    "tracker_optional": True,
                    "supported_privacy_frameworks": [],
                },
            ],
        )

        self.adgroup.refresh_from_db()
        for contentad in self.adgroup.contentad_set.all():
            self.assertEqual(
                contentad.trackers,
                [
                    {
                        "event_type": dash.constants.TrackerEventType.IMPRESSION,
                        "method": dash.constants.TrackerMethod.JS,
                        "url": "https://t.test.com/tracker.js",
                        "fallback_url": None,
                        "tracker_optional": False,
                        "supported_privacy_frameworks": [],
                    },
                    {
                        "event_type": dash.constants.TrackerEventType.IMPRESSION,
                        "method": dash.constants.TrackerMethod.JS,
                        "url": "https://z.moatads.com/publicisglobalbelgroupdcmdisplay84451019945/moatad.js#moatClientLevel1=8124669&moatClientLevel2=22196593&moatClientLevel3=238111095&moatClientLevel4=110934691&moatClientSlicer1=4490308&moatClientSlicer2=-&skin=0",
                        "fallback_url": None,
                        "tracker_optional": True,
                        "supported_privacy_frameworks": [],
                    },
                ],
            )

        self.account.refresh_from_db()
        for contentad in self.account.campaign_set.first().adgroup_set.first().contentad_set.all():
            self.assertEqual(
                contentad.trackers,
                [
                    {
                        "event_type": dash.constants.TrackerEventType.IMPRESSION,
                        "method": dash.constants.TrackerMethod.JS,
                        "url": "https://t.test.com/tracker.js",
                        "fallback_url": None,
                        "tracker_optional": False,
                        "supported_privacy_frameworks": [],
                    },
                    {
                        "event_type": dash.constants.TrackerEventType.IMPRESSION,
                        "method": dash.constants.TrackerMethod.JS,
                        "url": "https://pixel.adsafeprotected.com/jload?anId=930952&advId=6778&campId=[campaignid]&pubId=[publisher]",
                        "fallback_url": "https://pixel.adsafeprotected.com/?anId=930952&advId=6778&campId=[campaignid]&pubId=[publisher]",
                        "tracker_optional": True,
                        "supported_privacy_frameworks": [],
                    },
                ],
            )

        self.agency.refresh_from_db()
        for contentad in self.agency.account_set.first().campaign_set.first().adgroup_set.first().contentad_set.all():
            self.assertEqual(
                contentad.trackers,
                [
                    {
                        "event_type": dash.constants.TrackerEventType.IMPRESSION,
                        "method": dash.constants.TrackerMethod.JS,
                        "url": "https://t.test.com/tracker.js",
                        "fallback_url": None,
                        "tracker_optional": False,
                        "supported_privacy_frameworks": [],
                    },
                    {
                        "event_type": dash.constants.TrackerEventType.IMPRESSION,
                        "method": dash.constants.TrackerMethod.JS,
                        "url": "https://j.adlooxtracking.com/ads/js/tfav_adl_420.js#platform=12&scriptname=adl_420&tagid=728&typejs=tvaf&fwtype=1&creatype=2&targetelt=&custom1area=50&custom1sec=1&custom2area=0&custom2sec=0&id11=$ADLOOX_WEBSITE&id1=${PUBLISHER_ID}&id2=${CP_ID}&id3=${CREATIVE_ID}&id4=${CREATIVE_SIZE}&id5=${TAG_ID}&id6=${ADV_ID}&id7=${SELLER_MEMBER_ID}&id8=${CPG_ID}&id9=${USER_ID}",
                        "fallback_url": None,
                        "tracker_optional": True,
                        "supported_privacy_frameworks": [],
                    },
                ],
            )
