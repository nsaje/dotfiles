import datetime

import mock
from django.test import TestCase

import core.models
import dash.constants
from bs4 import BeautifulSoup
from integrations.product_feeds import constants
from integrations.product_feeds import exceptions
from utils import test_helper
from utils.magic_mixer import magic_mixer

from .model import ProductFeed


class ProductFeedTestCase(TestCase):
    def setUp(self):
        account = magic_mixer.blend(core.models.Account, id=123)
        campaign_1 = magic_mixer.blend(core.models.Campaign, account=account)

        self.ad_group_1 = magic_mixer.blend(core.models.AdGroup, campaign=campaign_1, id=1)
        self.ad_group_1.settings.update_unsafe(None, state=dash.constants.AdGroupSettingsState.ACTIVE, archived=False)
        self.ad_group_2 = magic_mixer.blend(core.models.AdGroup, campaign=campaign_1, id=2)
        self.ad_group_2.settings.update_unsafe(None, state=dash.constants.AdGroupSettingsState.INACTIVE, archived=False)

        with test_helper.disable_auto_now_add(core.models.ContentAd, "created_dt"):
            hash1 = ProductFeed._hash_label(
                "Existing title 1", "http://existingurl1.com", "http://existingimageurl1.com"
            )
            self.content_ad_1 = magic_mixer.blend(
                core.models.ContentAd,
                id=1,
                ad_group=self.ad_group_1,
                title="Existing title 1",
                url="http://existingurl1.com",
                image_url="http://existingimageurl1.com",
                state=dash.constants.ContentAdSourceState.ACTIVE,
                archived=False,
                label=hash1,
                created_dt=datetime.datetime(2019, 10, 23),
            )
            hash2 = ProductFeed._hash_label(
                "Existing title 2", "http://existingurl2.com", "http://existingimageurl2.com"
            )
            self.content_ad_2 = magic_mixer.blend(
                core.models.ContentAd,
                id=2,
                ad_group=self.ad_group_1,
                title="Existing title 2",
                url="http://existingurl2.com",
                image_url="http://existingimageurl2.com",
                archived=False,
                state=dash.constants.ContentAdSourceState.ACTIVE,
                label=hash2,
                created_dt=datetime.datetime(2019, 10, 23),
            )
            self.content_ad_3 = magic_mixer.blend(
                core.models.ContentAd,
                ad_group=self.ad_group_1,
                id=3,
                title="Existing title 3",
                url="http://existingurl3.com",
                image_url="http://existingimageurl3.com",
                state=dash.constants.ContentAdSourceState.INACTIVE,
                archived=True,
                created_dt=datetime.datetime(2019, 10, 23),
            )

        self.product_feed = ProductFeed(
            name="product_feed_test",
            feed_url="http://www.feed.com",
            feed_type=constants.FeedTypes.YAHOO_NEWS_RSS,
            default_brand_name="SomeBrand",
            blacklisted_keywords=["badword1", "Badword2"],
        )
        self.product_feed.save()
        self.product_feed.ad_groups.add(*[self.ad_group_1, self.ad_group_2])

    @mock.patch("integrations.product_feeds.models.ProductFeed._get_feed_data")
    def test_get_all_items(self, mock_feed_data):

        mock_feed_data.return_value = ""
        with self.assertRaisesMessage(exceptions.NofeedItems, "Not elements found with element names: 'item'"):
            self.product_feed._get_all_feed_items()

        mock_feed_data.return_value = """
        <html>
            <head>
            </head>
            <body>
                <script type="text/javascript">
                    location.replace('{{url|safe}}');
                </script>
            </body>
        </html>
        """
        with self.assertRaisesMessage(exceptions.NofeedItems, "Not elements found with element names: 'item'"):
            self.product_feed._get_all_feed_items()

        mock_feed_data.return_value = """
        <?xml version="1.0" encoding="UTF-8"?>
        <channel>
            <title>Yahoo News UK</title>
            <image>
                <title>Yahoo News UK &amp; Ireland - Latest World News &amp; UK News Headlines</title>
                <link>https://uk.news.yahoo.com</link>
                <url>https://s.yimg.com/rz/d/yahoo_news_en-GB_s_f_p_bestfit_news.png</url>
            </image>
            <thisisnotitem>
                <title>This is a title</title>
                <description>&lt;p&gt;&lt;a
                    href="https://uk.news.yahoo.com/police-manhunt-woman-raped-outside-161206935.html"&gt;desc 1&lt;p>
                </description>
                <link>https://uk.news.yahoo.com/police-manhunt-woman-raped-outside-161206935.html</link>
            </thisisnotitem>
            </channel>
        """
        with self.assertRaisesMessage(exceptions.NofeedItems, "Not elements found with element names: 'item'"):
            self.product_feed._get_all_feed_items()

    def test_get_parsed_item(self):
        # case all good with Yahoo news
        item1 = BeautifulSoup(
            """
        <item>
        <title>\tThis is a title \r\n</title>
        <description>&lt;p&gt;&lt;a
            href="https://uk.news.yahoo.com/police-manhunt-woman-raped-outside-1
            61206935.html"&gt;This is a description&lt;p>
        </description>
        <link>https://uk.news.yahoo.com/police-manhunt-woman-raped-outside-161206935.html</link>
        <pubDate>Mon, 21 Oct 2019 16:12:06 +0000</pubDate>
        <source url="http://www.standard.co.uk/">Evening Standard</source>
        <guid isPermaLink="false">police-manhunt-woman-raped-outside-161206935.html</guid>
        <media:content height="86"
                       url="http://l1.yimg.com/uu/api/res/1.2/3L5FebuCK.wH_eXbalJduw--/YXBwaWQ9eXRhY2h5b247aD04Njt3P
                       TEzMDs-/https://media.zenfs.com/en/evening_standard_239/a2aaa1d3edd79c203485271648b7f0ae"
                       width="130"
        />
        <media:credit role="publishing company"/>
        </item>
        """,
            features="xml",
        )
        parsed_item_1 = self.product_feed._get_parsed_item(item1)
        self.assertEqual(parsed_item_1["title"], "This is a title")
        self.assertEqual(parsed_item_1["description"], "This is a description")
        self.assertEqual(
            parsed_item_1["url"], "https://uk.news.yahoo.com/police-manhunt-woman-raped-outside-161206935.html"
        )
        self.assertEqual(
            parsed_item_1["image_url"],
            "https://media.zenfs.com/en/evening_standard_239/a2aaa1d3edd79c203485271648b7f0ae",
        )
        self.assertEqual(
            parsed_item_1["display_url"], "https://uk.news.yahoo.com/police-manhunt-woman-raped-outside-161206935.html"
        )
        self.assertEqual(parsed_item_1["brand_name"], "SomeBrand")
        self.assertEqual(parsed_item_1["call_to_action"], "Read more")

        # case all good with Yahoo sport
        item2 = BeautifulSoup(
            """
        <item>
        <title>\tThis is a title\r\n</title>
        <description>&lt;p&gt;&lt;a href="https://uk.news.yahoo.com/police-manhunt-woman-raped-outside-161206935.html"&gt;This is a description&lt;p></description>
        <link>https://uk.sports.yahoo.com/news/harry-kane-praises-ruthless-tottenham-as-spurs-hit-belgrade-for-five-212521294.html?src=rss</link>
        <content:encoded>&lt;article&gt;&lt;p&gt;&lt;a href="https://esportes.yahoo.com/noticias/galiotte-nao-deseja-demitir-mattos-neste-ano-090017163.html?src=rss"&gt;&lt;img src="https://s.yimg.com/uu/api/res/1.2/UL3x8xhXCB2uz136rgCl_A--~B/aD0xNTA0O3c9MjI1NjtzbT0xO2FwcGlkPXl0YWNoeW9u/https://s.yimg.com/os/creatr-uploaded-images/2019-10/02c636d0-fa90-11e9-acfd-7f9ed55815d1" width="2256" height="auto" style="max-width: 600px;"&gt;&lt;/img&gt;&lt;/a&gt;&lt;/p&gt;&lt;p&gt;Mesmo sendo pressionado pela torcida e por conselheiros, o presidente do Palmeiras não pensa em demitir seu diretor de futebol em 2019&lt;/p&gt;&lt;/article&gt;</content:encoded>        </item>
        """,
            features="xml",
        )
        self.product_feed.feed_type = constants.FeedTypes.YAHOO_SPORTS_RSS
        parsed_item_2 = self.product_feed._get_parsed_item(item2)
        self.assertEqual(parsed_item_2["title"], "This is a title")
        self.assertEqual(parsed_item_2["description"], "This is a description")
        self.assertEqual(
            parsed_item_2["url"],
            "https://uk.sports.yahoo.com/news/harry-kane-praises"
            "-ruthless-tottenham-as-spurs-hit-belgrade-for-five-212521294.html?src=rss",
        )
        self.assertEqual(
            parsed_item_2["image_url"],
            "https://s.yimg.com/uu/api/res/1.2/UL3x8xhXCB2uz136rgCl_A--~B/aD0xNTA0O3c9MjI1NjtzbT0xO2FwcGlkPXl0YWNoeW9u/https://s.yimg.com/os/creatr-uploaded-images/2019-10/02c636d0-fa90-11e9-acfd-7f9ed55815d1",
        )
        self.assertEqual(
            parsed_item_2["display_url"],
            "https://uk.sports.yahoo.com/news/harry-kane-praises-ruthless-totten"
            "ham-as-spurs-hit-belgrade-for-five-212521294.html?src=rss",
        )
        self.assertEqual(parsed_item_2["brand_name"], "SomeBrand")
        self.assertEqual(parsed_item_2["call_to_action"], "Read more")

        # case all good with Google feed
        item2 = BeautifulSoup(
            """
        <product>
            <id>245295</id>
            <title>\tThis is a title\r\n</title>
            <description>This is a description
            </description>
            <google_product_category>Apparel & Accessories > Clothing > Pants</google_product_category>
            <product_type>BOTTOMS</product_type>
            <link>https://www.uniqlo.com/sg/store/women-ezy-ankle-length-pants-4131210010.html</link>
            <image_link>https://d15udtvdbbfasl.cloudfront.net/catalog/product/large_image/09_413121.jpg</image_link>
            <condition>new</condition>
            <availability>in stock</availability>
            <price>49.90</price>
            <sale_price/>
            <brand>Uniqlo</brand>
            <mpn>413121</mpn>
            <gender/>
            <color>BLACK</color>
            <size>M</size>
            <size_type>Regular</size_type>
            <item_group_id>413121</item_group_id>
            <limited_offer>0</limited_offer>
            <online_exclusive>0</online_exclusive>
            <sale>0</sale>
            <new_arrivals>0</new_arrivals>
            <extra_size>1</extra_size>
            <inventory>11.0000</inventory>
            <flagship_exclusive>0</flagship_exclusive>
            <itemtype_1>Pants</itemtype_1>
            <itemtype_2>Ankle Pants</itemtype_2>
            <itemtype_3>Smart Pants</itemtype_3>
            <itemtype_4>New Year Style Guide</itemtype_4>
            <itemtype_5/>
        </product>
        """,
            features="xml",
        )
        self.product_feed.feed_type = constants.FeedTypes.GOOGLE_FEED
        parsed_item_2 = self.product_feed._get_parsed_item(item2)
        self.assertEqual(parsed_item_2["title"], "This is a title")
        self.assertEqual(parsed_item_2["description"], "This is a description")
        self.assertEqual(
            parsed_item_2["url"], "https://www.uniqlo.com/sg/store/women-ezy-ankle-length-pants-4131210010.html"
        )
        self.assertEqual(
            parsed_item_2["image_url"],
            "https://d15udtvdbbfasl.cloudfront.net/catalog/product/large_image/09_413121.jpg",
        )
        self.assertEqual(
            parsed_item_2["display_url"], "https://www.uniqlo.com/sg/store/women-ezy-ankle-length-pants-4131210010.html"
        )
        self.assertEqual(parsed_item_2["brand_name"], "Uniqlo")
        self.assertEqual(parsed_item_2["call_to_action"], "Read more")

    def test_parse_html_characters(self):
        item = BeautifulSoup(
            """
            <item>
                <title>Brexit : &quot;Les parlementaires britanniques ne veulent pas donner carte blanche à Boris Johnson&quot;, estime Jean-Louis Bourlanges (Modem)</title>
                <description>Yahoo Actualités - Toute l'actualité en France &amp; dans l&#8217;Europe</description>
            </item>
        """,
            features="xml",
        )
        parsed_item = self.product_feed._get_parsed_item(item)
        self.assertEqual(
            parsed_item["title"],
            'Brexit : "Les parlementaires britanniques ne veulent pas donner carte blanche à Boris Johnson", estime Jean-Louis Bourlanges (Modem)',
        )
        self.assertEqual(parsed_item["description"], "Yahoo Actualités - Toute l'actualité en France & dans l’Europe")
        self.assertEqual(parsed_item["url"], None)
        self.assertEqual(parsed_item["image_url"], None)
        self.assertEqual(parsed_item["display_url"], None)
        self.assertEqual(parsed_item["brand_name"], "SomeBrand")
        self.assertEqual(parsed_item["call_to_action"], "Read more")

    def test_parse_all_tags_empty(self):
        item = BeautifulSoup(
            """
            <item>
                <title></title>
                <description></description>
                <link></link>
                <media:content></media:content>
            </item>
        """,
            features="xml",
        )
        parsed_item = self.product_feed._get_parsed_item(item)
        self.assertIsNone(parsed_item["description"])
        self.assertIsNone(parsed_item["url"])
        self.assertIsNone(parsed_item["image_url"])
        self.assertIsNone(parsed_item["display_url"])
        self.assertEqual(parsed_item["brand_name"], "SomeBrand")
        self.assertEqual(parsed_item["call_to_action"], "Read more")

    def test_truncate(self):

        string_too_long = (
            "This a very long title, it has more than 90 characters, it needs to be truncated and 3 dots "
            "must be appended at the end. 90 chars is the limit for title and 150 is the limit"
            " of description!"
        )
        self.assertTrue(len(string_too_long) > 150)
        truncated_description = self.product_feed._truncate(string_too_long, constants.MAX_TITLE_LENGTH)
        self.assertEqual(len(truncated_description), 89)
        self.assertEqual(
            truncated_description,
            "This a very long title, it has more than 90 characters, it needs to be truncated and 3...",
        )

        truncated_description = self.product_feed._truncate(string_too_long, constants.MAX_DESCRIPTION_LENGTH)
        self.assertEqual(len(truncated_description), 149)
        self.assertEqual(
            truncated_description,
            "This a very long title, it has more than 90 characters, it needs to be truncated and 3 dots must be "
            "appended at the end. 90 chars is the limit for...",
        )

        string_too_short = "This is a string with less than 90 chars."
        truncated_description = self.product_feed._truncate(string_too_short, constants.MAX_TITLE_LENGTH)
        print(truncated_description)
        self.assertEqual(len(string_too_short), len(truncated_description))
        truncated_description = self.product_feed._truncate(string_too_short, constants.MAX_DESCRIPTION_LENGTH)
        self.assertEqual(len(string_too_short), len(truncated_description))

        exact_length = "a" * 90
        truncated_description = self.product_feed._truncate(exact_length, constants.MAX_TITLE_LENGTH)
        self.assertEqual(len(exact_length), len(truncated_description))
        exact_length = "a" * 150
        truncated_description = self.product_feed._truncate(exact_length, constants.MAX_DESCRIPTION_LENGTH)
        self.assertEqual(len(exact_length), len(truncated_description))

    def test_contains_blacklisted_words(self):
        string_with_blacklisted_words = "This is string contains badword1!"
        self.assertTrue(self.product_feed._contains_blacklisted_words(string_with_blacklisted_words))
        case_sensitive_badword = "BadWord2 in the string."
        self.assertTrue(self.product_feed._contains_blacklisted_words(case_sensitive_badword))

    def test_is_ad_already_uploaded(self):
        item = dict(title="Existing title 1", url="http://existingurl1.com", image_url="http://existingimageurl1.com")
        self.assertTrue(self.product_feed._is_ad_already_uploaded(item, self.ad_group_1))

        item = dict(title="Updated title", url="http://existingurl1.com", image_url="http://existingimageurl1.com")
        self.assertFalse(self.product_feed._is_ad_already_uploaded(item, self.ad_group_1))

    def test_validate_item(self):
        item = dict(title="Existing title", url="http://existingurl.com", image_url="http://existingimageurl.com")
        with self.assertRaisesMessage(exceptions.ValidationError, "Item has missing key(s)"):
            self.product_feed._validate_item(item)

        item = dict(
            title="Existing title",
            url="http://existingurl.com",
            image_url="http://existingimageurl.com",
            description="description",
            display_url=None,
        )
        with self.assertRaisesMessage(exceptions.ValidationError, "Item has empty values."):
            self.product_feed._validate_item(item)

        item = dict(
            title="badword1",
            url="http://existingurl.com",
            image_url="http://existingimageurl.com",
            description="description",
            display_url="http://displayurl.com",
        )
        with self.assertRaisesMessage(exceptions.ValidationError, "Title contains blacklisted keywords."):
            self.product_feed._validate_item(item)

        item = dict(
            title="Existing title",
            url="http://existingurl.com",
            image_url="http://existingimageurl.com",
            description="description",
            display_url="http://displayurl.com",
        )
        self.assertTrue(self.product_feed._validate_item(item))

    @mock.patch("integrations.product_feeds.models.ProductFeed._write_log")
    @mock.patch("utils.dates_helper.local_today")
    def test_pause_and_archive_ads(self, mock_today, mock_write_log):
        mock_today.return_value = datetime.datetime(2019, 10, 27)
        self.product_feed.content_ads_ttl = 2

        self.product_feed.pause_and_archive_ads(dry_run=True)
        mock_write_log.assert_called_with(dry_run=True, ads_paused_and_archived=[self.content_ad_1, self.content_ad_2])

        self.product_feed.pause_and_archive_ads(dry_run=False)
        self.content_ad_1.refresh_from_db()
        self.assertTrue(self.content_ad_1.state == dash.constants.ContentAdSourceState.INACTIVE)
        self.assertTrue(self.content_ad_1.archived)
        self.content_ad_2.refresh_from_db()
        self.assertTrue(self.content_ad_2.state == dash.constants.ContentAdSourceState.INACTIVE)
        self.assertTrue(self.content_ad_2.archived)
        self.content_ad_3.refresh_from_db()
        self.assertTrue(self.content_ad_3.state == dash.constants.ContentAdSourceState.INACTIVE)
        self.assertTrue(self.content_ad_3.archived)
        mock_write_log.assert_called_with(dry_run=False, ads_paused_and_archived=[self.content_ad_1, self.content_ad_2])

    @mock.patch("integrations.product_feeds.models.ProductFeed._write_log")
    @mock.patch("utils.dates_helper.local_now")
    @mock.patch("integrations.product_feeds.models.ProductFeed._get_feed_data")
    def test_ingest_and_create_ads_yahoo(self, mock_feed_data, mock_today, mock_write_log):
        mock_today.return_value = datetime.datetime(2019, 10, 24, 10, 25)
        mock_feed_data.return_value = """
        <?xml version="1.0" encoding="UTF-8"?>
        <rss xmlns:media="http://search.yahoo.com/mrss/" version="2.0">
            <channel>
                <title>Yahoo News UK</title>
                <link>https://uk.news.yahoo.com</link>
                <description>The latest world news and UK...
                </description>
                <language>en-GB</language>
                <copyright>Copyright (c) 2019 Yahoo! Inc. All rights reserved</copyright>
                <pubDate>Tue, 22 Oct 2019 08:46:33 +0000</pubDate>
                <ttl>5</ttl>
                <image>
                    <title>Yahoo News UK &amp; Ireland - Latest World News &amp; UK News Headlines</title>
                    <link>https://uk.news.yahoo.com</link>
                    <url>https://s.yimg.com/rz/d/yahoo_news_en-GB_s_f_p_bestfit_news.png</url>
                </image>
                <item>
                    <title>This is a title</title>
                    <description>desc 1 </description>
                    <link>https://uk.news.yahoo.com/police-manhunt-woman-raped-outside-161206935.html</link>
                    <pubDate>Mon, 21 Oct 2019 16:12:06 +0000</pubDate>
                    <source url="http://www.standard.co.uk/">Evening Standard</source>
                    <guid isPermaLink="false">police-manhunt-woman-raped-outside-161206935.html</guid>
                    <media:content height="86"
                                   url="http://l1.yimg.com/uu/api/res/1.2/3L5FebuCK.wH_eXbalJduw--/YXBwaWQ9eXRhY2h5b247aD04Njt3PTEzMDs-/https://media.zenfs.com/en/evening_standard_239/a2aaa1d3edd79c203485271648b7f0ae"
                                   width="130"/>
                    <media:credit role="publishing company"/>
                </item>
                <item>
                    <title>title 2</title>
                    <description>This is a description\n</description>
                    <link>https://uk.news.yahoo.com/botswana-faces-first-tight-election-173231503.html</link>
                    <pubDate>Mon, 21 Oct 2019 17:32:31 +0000</pubDate>
                    <source url="http://www.france24.com/en/">France 24</source>
                    <guid isPermaLink="false">botswana-faces-first-tight-election-173231503.html</guid>
                    <media:content height="86"
                                   url="http://l.yimg.com/uu/api/res/1.2/4v359gKa05EvvOmY0HoVUw--/YXBwaWQ9eXRhY2h5b247aD04Njt3PTEzMDs-/https://media.zenfs.com/en/france_24_english_articles_100/4f075adb1f596cc00b81cc7e58406716"
                                   width="130"/>
                    <media:credit role="publishing company"/>
                </item>
                <item>
                    <title></title>
                    <description>has broken title</description>
                    <link>https://uk.news.yahoo.com/driver-walks-free-after-killing-motorcyclist-sat-nav-150735231.html</link>
                    <pubDate>Mon, 21 Oct 2019 15:07:35 +0000</pubDate>
                    <source url="https://uk.news.yahoo.com/">Yahoo News UK</source>
                    <guid isPermaLink="false">driver-walks-free-after-killing-motorcyclist-sat-nav-150735231.html</guid>
                    <media:content height="86"
                                   url="http://l1.yimg.com/uu/api/res/1.2/yyWa.Yt4dRgc5K85UhaMSQ--/YXBwaWQ9eXRhY2h5b247aD04Njt3PTEzMDs-/"
                                   width="130"/>
                    <media:credit role="publishing company"/>
                </item>
                <item>
                    <title>has no image link</title>
                    <description>description 4</description>
                    <link>https://uk.news.yahoo.com/driver-walks-free-after-killing-motorcyclist-sat-nav-150735231.html</link>
                    <pubDate>Mon, 21 Oct 2019 15:07:35 +0000</pubDate>
                    <source url="https://uk.news.yahoo.com/">Yahoo News UK</source>
                    <guid isPermaLink="false">driver-walks-free-after-killing-motorcyclist-sat-nav-150735231.html</guid>
                    <media:content height="86"
                                   width="130"/>
                    <media:credit role="publishing company"/>
                </item>
                <item>
                    <title>Existing title 1</title>
                    <description>&lt;p&gt;&lt;a
                        href="https://uk.news.yahoo.com/police-manhunt-woman-raped-outside-161206935.html"&gt;desc 1&lt;p>
                    </description>
                    <link>http://existingurl1.com</link>
                    <pubDate>Mon, 21 Oct 2019 16:12:06 +0000</pubDate>
                    <source url="http://www.standard.co.uk/">Evening Standard</source>
                    <guid isPermaLink="false">police-manhunt-woman-raped-outside-161206935.html</guid>
                    <media:content height="86"
                                   url="http://existingimageurl1.com"
                                   width="130"/>
                    <media:credit role="publishing company"/>
                </item>
                <item></item>
            </channel>
        </rss>
        """
        self.product_feed.ingest_and_create_ads()
        self.assertTrue(
            core.models.ContentAdCandidate.objects.filter(
                title="This is a title",
                description="desc 1",
                url="https://uk.news.yahoo.com/police-manhunt-woman-raped-outside-161206935.html",
                display_url="https://uk.news.yahoo.com/police-manhunt-woman-raped-outside-161206935.html",
                image_url="https://media.zenfs.com/en/evening_standard_239/a2aaa1d3edd79c203485271648b7f0ae",
                brand_name="SomeBrand",
            ).exists()
        )
        self.assertTrue(
            core.models.ContentAdCandidate.objects.filter(
                title="title 2",
                description="This is a description",
                url="https://uk.news.yahoo.com/botswana-faces-first-tight-election-173231503.html",
                display_url="https://uk.news.yahoo.com/botswana-faces-first-tight-election-173231503.html",
                image_url="https://media.zenfs.com/en/france_24_english_articles_100/4f075adb1f596cc00b81cc7e58406716",
                brand_name="SomeBrand",
            ).exists()
        )
        self.assertFalse(
            core.models.ContentAdCandidate.objects.filter(
                description="has broken title",
                url="https://uk.news.yahoo.com/driver-walks-free-after-killing-motorcyclist-sat-nav-150735231.html",
            ).exists()
        )
        self.assertFalse(core.models.ContentAdCandidate.objects.filter(title="has no image link").exists())
        self.assertFalse(
            core.models.ContentAdCandidate.objects.filter(
                title="Existing title 1", url="http://existingurl1.com"
            ).exists()
        )
        self.assertTrue(
            core.models.UploadBatch.objects.filter(
                name="product_feed_test_2019-10-24-1025", status=dash.constants.UploadBatchStatus.IN_PROGRESS
            ).exists()
        )

        self.assertEqual(core.models.ContentAdCandidate.objects.count(), 2)
        self.assertEqual(mock_write_log.call_count, 1)

    @mock.patch("integrations.product_feeds.models.ProductFeed._write_log")
    @mock.patch("utils.dates_helper.local_now")
    @mock.patch("integrations.product_feeds.models.ProductFeed._get_feed_data")
    def test_ingest_and_create_ads_google(self, mock_feed_data, mock_today, mock_write_log):
        self.product_feed.feed_type = constants.FeedTypes.GOOGLE_FEED
        self.product_feed.truncate_description = True
        mock_today.return_value = datetime.datetime(2019, 10, 24, 10, 25)
        mock_feed_data.return_value = """
            <product>
                <id>245294</id>
                <title>WOMEN EZY Ankle Pants</title>
                <description>A sleek cut with superb comfort, our EZY ankle pantscome in versatile solid colors.<br>-
                Updated for a new season with a flattering cut in back.<br>- Wrinkle-resistant
                rayon blend material with stretch for easy movement.<br>- Elegant wool-like texture.<br>- Newly-developed fabric with
                just the right heft for any temperature.<br>- Lightweight elastic waistband blends in with the fabric for a consistent
                look.
                </description>
                <google_product_category>Apparel & Accessories > Clothing > Pants</google_product_category>
                <product_type>
                BOTTOMS
                </product_type>
                <link>https://www.uniqlo.com/sg/store/women-ezy-ankle-length-pants-4131210009.html</link
                ><image_link>
                https://d15udtvdbbfasl.cloudfront.net/catalog/product/large_image/09_413121.jpg
                </image_link>
                <condition>new</condition><availability>in stock</availability><price>49.90</price><sale_price/>
                <brand> Uniqlo</brand
            </product>
            <product>
                <id>245295</id>
                <title>Existing title 2</title>
                <description>A sleek cut with superb comfort, our EZY ankle pants come in versatile solid colors.<br>- Updated for a new
                    season with a flattering cut in back.<br>- Wrinkle-resistant rayon blend material with stretch for easy movement.
                    <br>- Elegant wool-like texture.<br>- Newly-developed fabric with just the right heft for any temperature.<br>-
                    Lightweight elastic waistband blends in with the fabric for a consistent look.
                </description>
                <google_product_category>Apparel & Accessories > Clothing > Pants</google_product_category>
                <product_type>BOTTOMS</product_type>
                <link>http://existingurl2.com</link>
                <image_link>http://existingimageurl2.com</image_link>
                <condition>new</condition>
                <availability>in stock</availability>
                <price>49.90</price>
                <sale_price/>
                <brand>Uniqlo</brand>
            </product>
            <product></product>
        """
        self.product_feed.ingest_and_create_ads()
        ad = core.models.ContentAdCandidate.objects.get(
            title="WOMEN EZY Ankle Pants",
            url="https://www.uniqlo.com/sg/store/women-ezy-ankle-length-pants-4131210009.html",
            display_url="https://www.uniqlo.com/sg/store/women-ezy-ankle-length-pants-4131210009.html",
            image_url="https://d15udtvdbbfasl.cloudfront.net/catalog/product/large_image/09_413121.jpg",
            brand_name="Uniqlo",
        )
        self.assertTrue(ad)
        self.assertTrue(len(ad.description) <= 150)
        self.assertFalse(
            core.models.ContentAdCandidate.objects.filter(
                title="Existing title 2", url="http://existingurl2.com", image_url="http://existingimageurl2.com"
            ).exists()
        )

        self.assertTrue(
            core.models.UploadBatch.objects.filter(
                name="product_feed_test_2019-10-24-1025", status=dash.constants.UploadBatchStatus.IN_PROGRESS
            ).exists()
        )
        self.assertEqual(core.models.ContentAdCandidate.objects.count(), 1)
        self.assertEqual(mock_write_log.call_count, 1)
