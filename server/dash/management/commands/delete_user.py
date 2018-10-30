import django.apps
from django.db.models import Model
from django.db.models import QuerySet
from django.utils.six.moves import input

import core.features.history
from utils.command_helpers import ExceptionCommand
from zemauth import models

DELETED_USER_ID = 1553


class Command(ExceptionCommand):

    help = "Deletes user and all references permanently from db"

    def add_arguments(self, parser):
        parser.add_argument("user_id", type=int, help="Reports receiver e-mail.")

    def handle(self, *args, **options):
        deleted_user = models.User.objects.get(pk=DELETED_USER_ID)
        print("Using %s for deleted user." % deleted_user)

        user = models.User.objects.get(pk=options["user_id"])
        if not self._confirm_delete(user):
            return

        history_models, relation_names = self._change_db_relations(user, deleted_user)

        for history_model in history_models:
            self._change_ids_in_history_model_subclass(user, deleted_user, history_model, relation_names)

        self._change_ids_and_text_in_history(user, deleted_user, relation_names)

        print("Deleting user")
        user.delete()

    def _confirm_delete(self, user):
        result = input("You are about to delete user %s. Do you want to continue?[y/N]" % user)
        return len(result) > 0 and result[0].lower() == "y"

    def _change_db_relations(self, user, deleted_user):
        print("Changing relations")
        relation_names = set()
        history_models = []
        for model in django.apps.apps.get_models():
            if issubclass(model, core.features.history.HistoryModel):
                history_models.append(model)
            for field in model._meta.get_fields():
                if self._is_user_relation(model, field):
                    key = field.name
                    relation_names.add(key)
                    QuerySet(model).filter(**{key: user}).update(**{key: deleted_user})
        return history_models, relation_names

    def _is_user_relation(self, model, field):
        if not field.auto_created and field.related_model == models.User:
            if field.many_to_one:
                return True
            elif field.many_to_many:
                return False
            else:
                raise Exception("Unsupported relation %s on %s" % (field, model))
        return False

    def _change_ids_in_history_model_subclass(self, user, deleted_user, history_model, relation_names):
        i = 0
        total = history_model.objects.all().count()
        for history in history_model.objects.all().iterator():
            changed = False
            if history.snapshot:
                for field in relation_names:
                    if field not in history.snapshot:
                        continue
                    if history.snapshot[field] == user.id:
                        history.snapshot[field] = deleted_user.id
                        changed = True
            if changed:
                Model.save(history)

            if i % 10000 == 0:
                print("Going over %s: %d/%d" % (history_model.__name__, i, total))
            i += 1

    def _change_ids_and_text_in_history(self, user, deleted_user, relation_names):
        i = 0
        total = core.features.history.History.objects.all().count()
        for history in core.features.history.History.objects.all().iterator():
            changed = False
            if history.changes:
                for field in relation_names:
                    if field not in history.changes:
                        continue
                    if history.changes[field] == user.id:
                        history.changes[field] = deleted_user.id
                        changed = True

            old_text = history.changes_text
            if user.email:
                history.changes_text = history.changes_text.replace(user.email, deleted_user.email)
            if user.get_full_name():
                history.changes_text = history.changes_text.replace(user.get_full_name(), deleted_user.get_full_name())
            if history.changes_text != old_text:
                changed = True

            if changed:
                Model.save(history)

            if i % 10000 == 0:
                print("Going over history: %d/%d" % (i, total))
            i += 1
