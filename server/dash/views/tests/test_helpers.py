# import datetime
# import pytz

# from django.test import TestCase
# from django.conf import settings

# from dash.views import helpers
# from dash import models


# class ViewHelpersTestCase(TestCase):
#     fixtures = ['test_api.yaml']

#     def test_get_ad_group_sources_data_status(self):
#         ad_group_source1 = models.AdGroupSource.objects.get(pk=1)
#         ad_group_source2 = models.AdGroupSource.objects.get(pk=2)
#         ad_group_source3 = models.AdGroupSource.objects.get(pk=3)

#         data_status = helpers.get_ad_group_sources_data_status(
#             [ad_group_source1, ad_group_source2, ad_group_source3],
#             include_state_messages=True)

#         self.assertEqual(data_status[ad_group_source1.source_id]['ok'], False)

#         self.assertEqual(
#             data_status[ad_group_source1.source_id]['message'],
#             '<b>Status</b> for this Media Source differs from Status in the Media Source\'s 3rd party dashboard.<br/>Reporting data is stale. Last OK sync was on: <b>06/10/2014 5:58 AM</b>'
#         )

#         self.assertEqual(
#             data_status[ad_group_source2.source_id]['message'],
#             '<b>Bid CPC</b> for this Media Source differs from Bid CPC in the Media Source\'s 3rd party dashboard.<br/><b>Daily Budget</b> for this Media Source differs from Daily Budget in the Media Source\'s 3rd party dashboard.<br/>Reporting data is stale. Last OK sync was on: <b>06/10/2014 5:58 AM</b>'
#         )

#         self.assertEqual(
#             data_status[ad_group_source3.source_id]['message'],
#             'Reporting data is stale. Last OK sync was on: <b>06/10/2014 5:58 AM</b>'
#         )

#     def test_get_ad_group_sources_data_status_cannot_edit_cpc_budget(self):
#         ad_group_source = models.AdGroupSource.objects.get(pk=2)

#         # clear all available actions - this makes editing disabled
#         ad_group_source.source.source_type.available_actions.clear()

#         data_status = helpers.get_ad_group_sources_data_status(
#             [ad_group_source],
#             include_state_messages=True)

#         self.assertEqual(
#             data_status[ad_group_source.source_id]['message'],
#             'Reporting data is stale. Last OK sync was on: <b>06/10/2014 5:58 AM</b>'
#         )

#     def test_get_ad_group_sources_data_status_not_stale(self):
#         ad_group_source = models.AdGroupSource.objects.get(pk=3)

#         last_sync = datetime.datetime.now()
#         ad_group_source.last_successful_sync_dt = last_sync

#         data_status = helpers.get_ad_group_sources_data_status([ad_group_source], include_state_messages=True)

#         self.assertEqual(data_status[ad_group_source.source_id]['ok'], True)

#         datetime_string = pytz.utc.localize(last_sync).astimezone(pytz.timezone(settings.DEFAULT_TIME_ZONE))

#         self.assertEqual(
#             data_status[ad_group_source.source_id]['message'],
#             'All data is OK. Last OK sync was on: <b>{}</b>'.format(
#                 datetime_string.strftime('%m/%d/%Y %-I:%M %p'))
#         )

#     def test_get_ad_group_sources_data_status_no_settings(self):
#         ad_group_source = models.AdGroupSource.objects.get(pk=4)

#         data_status = helpers.get_ad_group_sources_data_status([ad_group_source], include_state_messages=True)

#         self.assertEqual(data_status[ad_group_source.source_id]['ok'], False)

#         self.assertEqual(
#             data_status[ad_group_source.source_id]['message'],
#             'Reporting data is stale. Last OK sync was on: <b>06/10/2014 5:58 AM</b>'
#         )

#     def test_get_ad_group_sources_data_status_property_none(self):
#         ad_group_source = models.AdGroupSource.objects.get(pk=4)
#         data_status = helpers.get_ad_group_sources_data_status([ad_group_source], include_state_messages=True)

#         self.assertEqual(data_status[ad_group_source.source_id]['ok'], False)

#         self.assertEqual(
#             data_status[ad_group_source.source_id]['message'],
#             'Reporting data is stale. Last OK sync was on: <b>06/10/2014 5:58 AM</b>'
#         )
