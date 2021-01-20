import sys

from django.core import management

from dcron import helpers
from dcron.commands import DCronCommand


class Command(DCronCommand):
    help = "DCronCommand launcher is a proxy to another management command that does not extend DCronCommand."

    def __init__(self, stdout=None, stderr=None, no_color=False, force_color=None):
        self.proxy_command_name = helpers.get_command(sys.argv)
        self._execute_recursion_check()
        super().__init__(stdout=stdout, stderr=stderr, no_color=no_color, force_color=None)

    def add_arguments(self, parser):
        parser.add_argument("proxy_command_name", help="The name of management command to run.")
        self._add_proxy_command_arguments(parser)

    def _handle(self, *args, **options):
        management.call_command(self.proxy_command_name, *helpers.get_arguments(sys.argv))

    def _get_command_name(self):
        return self.proxy_command_name

    def _add_proxy_command_arguments(self, parser):
        try:
            app_name = management.get_commands()[self.proxy_command_name]
        except KeyError:
            raise management.CommandError("Unknown command: %s" % self.proxy_command_name)

        command = management.load_command_class(app_name, self.proxy_command_name)

        if isinstance(command, DCronCommand):
            raise management.CommandError("%s is already DCronCommand" % self.proxy_command_name)

        command.add_arguments(parser)

    def _execute_recursion_check(self):
        if self.proxy_command_name == __name__.split(".")[-1]:
            raise management.CommandError("%s can not be called on itself" % self.proxy_command_name)
