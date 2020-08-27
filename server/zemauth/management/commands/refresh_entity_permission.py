# -*- coding: utf-8 -*-

import zemauth.models
from utils import zlogging
from utils.command_helpers import Z1Command
from utils.queryset_helper import chunk_iterator

BATCH_SIZE = 100

logger = zlogging.getLogger(__name__)


class Command(Z1Command):
    help = "Refresh entitypermission table"

    def handle(self, *args, **options):
        logger.info("Refreshing entitypermission table started...")

        users_qs = zemauth.models.User.objects.all()

        chunk_number = 0
        for users_chunk in chunk_iterator(users_qs.distinct(), chunk_size=BATCH_SIZE):
            chunk_number += 1
            logger.info("Processing chunk number %s...", chunk_number)
            for user in users_chunk:
                user.refresh_entity_permissions()

        logger.info("Refreshing entitypermission table completed...")
