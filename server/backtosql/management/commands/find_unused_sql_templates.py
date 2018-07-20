import fileinput
import operator
import os
from django.core.management.base import BaseCommand


TEMPLATES_PREFIX = "templates/"


class Command(BaseCommand):
    help = "Finds all unused templates"

    def handle(self, *args, **options):

        templates = get_templates()
        files = get_py_files()
        usage = {t: 0 for t in templates}

        for line in fileinput.input(files):
            for template in templates:
                name = get_template_name(template)

                if name in line:
                    usage[template] += 1

        print("Times used\tTemplate path")
        for template, counter in sorted(list(usage.items()), reverse=True, key=operator.itemgetter(1, 0)):
            print(("{:>10}\t{}".format(counter, template)))


def get_template_name(path):
    return path.rsplit(TEMPLATES_PREFIX)[1]


def get_templates(extension=".sql"):
    return [
        f[2:-1] for f in os.popen("find . -name '*{}' | sort".format(extension)).readlines() if TEMPLATES_PREFIX in f
    ]


def get_py_files():
    return [f[2:-1] for f in os.popen("find . -name '*.py' | sort").readlines()]
