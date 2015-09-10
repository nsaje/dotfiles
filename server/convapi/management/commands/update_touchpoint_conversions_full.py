import logging

from django.core.management.base import BaseCommand

from convapi import process

logger = logging.getLogger(__name__)


class Command(BaseCommand):

    def handle(self, *args, **options):
        process.update_touchpoint_conversions_full()
