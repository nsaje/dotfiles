import demo
from utils.command_helpers import Z1Command


class Command(Z1Command):
    def handle(self, *args, **options):
        demo.terminate_old_instances()
