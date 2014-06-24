from django.core.management.base import BaseCommand
from optparse import make_option


class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--ad_group_ids',),
        make_option('--date',)
    )

    def handle(self, *args, **options):
        raise NotImplementedError
