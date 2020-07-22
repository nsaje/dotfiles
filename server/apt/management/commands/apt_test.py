import os

from django.conf import settings

import apt.base.runner
from utils import zlogging
from utils.command_helpers import Z1Command

logger = zlogging.getLogger(__name__)


class Command(Z1Command):
    help = "Discover and run Automatic Production Tests"

    def add_arguments(self, parser):
        parser.add_argument(
            "args",
            metavar="test_label",
            nargs="*",
            help="Module paths to test; can be modulename, modulename.TestCase or modulename.TestCase.test_method",
        )
        apt.base.runner.APTTestRunner.add_arguments(parser)

    def handle(self, *test_labels, **options):
        runner = apt.base.runner.APTTestRunner(output=os.path.join(settings.APT_TESTS_PATH, ".junit_xml"), **options)
        runner.run_tests(test_labels)
