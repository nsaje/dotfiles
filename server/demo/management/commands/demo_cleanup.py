import demo
from utils.command_helpers import ExceptionCommand


class Command(ExceptionCommand):
    def handle(self, *args, **options):
        demo.terminate_old_instances()
