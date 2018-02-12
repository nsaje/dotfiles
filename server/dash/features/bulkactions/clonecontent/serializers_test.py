from django.test import TestCase
import rest_framework.serializers
from utils.magic_mixer import magic_mixer
from utils import test_helper

import core.entity
from . import serializers


class CloneContentAdsSerializer(TestCase):

    def test_validate_select_all(self):
        form = serializers.CloneContentAdsSerializer(data={
            'ad_group_id': '123',
            'destination_ad_group_id': '223',
            'destination_batch_name': 'asd',
        })

        form.is_valid(raise_exception=True)
        self.assertEqual(form.validated_data, {
            'ad_group_id': 123,
            'destination_ad_group_id': 223,
            'destination_batch_name': 'asd',
        })

    def test_validate_select_batch(self):
        form = serializers.CloneContentAdsSerializer(data={
            'ad_group_id': '123',
            'destination_ad_group_id': '223',
            'destination_batch_name': 'asd',
            'batch_id': '1',
        })

        form.is_valid(raise_exception=True)
        self.assertEqual(form.validated_data, {
            'ad_group_id': 123,
            'destination_ad_group_id': 223,
            'destination_batch_name': 'asd',
            'batch_id': 1,
        })

    def test_validate_select_content_ads(self):
        form = serializers.CloneContentAdsSerializer(data={
            'ad_group_id': '123',
            'destination_ad_group_id': '223',
            'destination_batch_name': 'asd',
            'content_ad_ids': ['1'],
        })

        form.is_valid(raise_exception=True)
        self.assertEqual(form.validated_data, {
            'ad_group_id': 123,
            'destination_ad_group_id': 223,
            'destination_batch_name': 'asd',
            'content_ad_ids': [1],
        })


class GetContentAds(TestCase):

    def setUp(self):
        self.ads = magic_mixer.cycle(5).blend(core.entity.ContentAd, batch=magic_mixer.RANDOM)

    def test_get_select_all(self):
        self.assertEqual(
            test_helper.QuerySetMatcher(
                serializers.get_content_ads(core.entity.ContentAd.objects.all(), {})),
            self.ads)

    def test_get_select_ads(self):
        self.assertEqual(
            test_helper.QuerySetMatcher(
                serializers.get_content_ads(core.entity.ContentAd.objects.all(), {
                    'content_ad_ids': [self.ads[0].id],
                })),
            [self.ads[0]])

    def test_get_select_batch(self):
        self.assertEqual(
            test_helper.QuerySetMatcher(
                serializers.get_content_ads(core.entity.ContentAd.objects.all(), {
                    'batch_id': self.ads[0].batch_id,
                })),
            [x for x in self.ads if x.batch_id == self.ads[0].batch_id])

    def test_get_deselected_ads(self):
        self.assertEqual(
            test_helper.QuerySetMatcher(
                serializers.get_content_ads(core.entity.ContentAd.objects.all(), {
                    'deselected_content_ad_ids': [self.ads[0].id],
                })),
            self.ads[1:])

    def test_get_deselected_from_batch(self):
        self.assertEqual(
            test_helper.QuerySetMatcher(
                serializers.get_content_ads(core.entity.ContentAd.objects.all(), {
                    'batch_id': self.ads[0].batch_id,
                    'deselected_content_ad_ids': [self.ads[1].id],
                })),
            [x for x in self.ads if x.batch_id == self.ads[0].batch_id and x.id != self.ads[1].id])

    def test_no_ads(self):
        with self.assertRaises(rest_framework.serializers.ValidationError):
            serializers.get_content_ads(core.entity.ContentAd.objects.none(), {})

    def test_all_deselected(self):
        ads = core.entity.ContentAd.objects.all()
        with self.assertRaises(rest_framework.serializers.ValidationError):
            serializers.get_content_ads(ads, {
                'deselected_content_ad_ids': [x.id for x in ads],
            })
