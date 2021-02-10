import sys

from django.template import Context
from django.template import Template

import core.features.delivery_status
import dash.constants
from utils import constant_base
from utils import zlogging
from utils.command_helpers import Z1Command

logger = zlogging.getLogger(__name__)


class Command(Z1Command):

    help = "Fetches new constants data from models and builds blueprint for restapi"

    def add_arguments(self, parser):
        parser.add_argument("blueprint_file", type=str, help="example filename: api_blueprint.md")

    def handle(self, *args, **options):
        file_path = options["blueprint_file"]

        file_content = open(file_path, "r").read()
        context = Context(
            {
                "constants": {
                    "currency": self.generate_constants_section(dash.constants.Currency),
                    "osv": self.generate_constants_section(dash.constants.OperatingSystemVersion),
                    "os": self.generate_constants_section(dash.constants.OperatingSystem),
                    "delivery": self.generate_constants_section(core.features.delivery_status.DeliveryStatus),
                    "trackerEventType": self.generate_constants_section(dash.constants.TrackerEventType),
                    "trackerMethod": self.generate_constants_section(dash.constants.TrackerMethod),
                }
            }
        )
        template = Template(file_content)
        sys.stdout.write(template.render(context))
        sys.stdout.flush()

    def generate_constants_section(self, constants_model: constant_base.ConstantBase):
        constant_dict = dict()
        for constant in constants_model.get_all():
            if constant:
                constant_dict[constants_model.get_name(constant)] = constants_model.get_text(constant)
        return constant_dict
