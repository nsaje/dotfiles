#!/usr/bin/env python
import os
import sys

import warnings # filtering out warnings when loading YAML fixtures with USE_TZ = True
warnings.filterwarnings('ignore', r"DateTimeField .* received a naive datetime", RuntimeWarning, r'django\.db\.models\.fields')

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "server.settings")

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)

    
