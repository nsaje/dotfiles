from io import StringIO

from django.core import management

from ..base.test_case import APTTestCase


class DBMigrationsAPTTest(APTTestCase):
    def test_migrations_applied(self):
        string_io = StringIO()
        # TODO when we upgrade Django, we should call "migrate --check" instead
        management.call_command("showmigrations", stdout=string_io)
        string_io.seek(0)
        output = string_io.read()
        for line in output.splitlines():
            if "[ ]" in line:
                self.fail("There are unapplied DB migrations!")
