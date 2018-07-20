#!/usr/bin/env python
import os
import sys
import cdecimal

# Ensure any import of decimal gets cdecimal instead.
sys.modules["decimal"] = cdecimal

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "server.settings")

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
