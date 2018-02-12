import os
import imp
import sys

"""
This module is only _proxy_ for real localsettings.
"""

sys.dont_write_bytecode = True


def is_valid_attribute(attribute_name):
    if attribute_name.startswith("_"):
        return False
    return attribute_name.upper() == attribute_name


def discover_localsettings_path(suffix='docker'):
    localsettings_path = os.path.dirname(os.path.abspath(__file__))
    localsettings_filename = "{path}/localsettings.py.{env}".format(
        path=localsettings_path,
        env=suffix
    )
    return localsettings_filename


_LOCALSETTINGS_FILENAME = discover_localsettings_path(
    os.environ.get('CONF_ENV', 'docker'))
print("Loading configuration from {filename}".format(filename=_LOCALSETTINGS_FILENAME), file=sys.stderr)
module = imp.load_source("localsettings", _LOCALSETTINGS_FILENAME)

for attribute in dir(module):
    if is_valid_attribute(attribute):
        globals()[attribute] = getattr(module, attribute)
