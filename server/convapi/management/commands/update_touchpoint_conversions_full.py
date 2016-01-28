import logging

from django.core.management.base import BaseCommand

from convapi import process
from utils.command_helpers import ExceptionCommand

logger = logging.getLogger(__name__)


class Command(ExceptionCommand):

    def handle(self, *args, **options):
        process.update_touchpoint_conversions_full()
