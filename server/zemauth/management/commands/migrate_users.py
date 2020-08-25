from django.contrib.auth import models as auth_models
from django.db.models import Q

import core.models
import zemauth.models
from utils import zlogging
from utils.command_helpers import Z1Command
from utils.queryset_helper import chunk_iterator

BATCH_SIZE = 100

logger = zlogging.getLogger(__name__)


class Command(Z1Command):
    help = "Migrate users to entity permissions"

    def add_arguments(self, parser):
        parser.add_argument("--agency_id", type=int)

    def handle(self, *args, **options):
        logger.info("Star migrating users to entity permissions...")

        agency_id = options.get("agency_id")
        agency = core.models.Agency.objects.get(pk=agency_id)
        users_qs = (
            zemauth.models.User.objects.filter(Q(agency__id=agency.id) | Q(account__agency__id=agency.id))
            .filter(is_active=True)
            .distinct()
        )

        chunk_number = 0
        for users_chunk in chunk_iterator(users_qs, chunk_size=BATCH_SIZE):
            chunk_number += 1
            logger.info("Processing chunk number %s...", chunk_number)
            for user in users_chunk:
                user.refresh_entity_permissions()
                user.user_permissions.add(auth_models.Permission.objects.get(codename="fea_use_entity_permission"))
                user.user_permissions.add(auth_models.Permission.objects.get(codename="can_see_user_management"))

        logger.info("Users migration to entity permissions completed...")