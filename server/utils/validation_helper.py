import re

from django.core.exceptions import ValidationError

HTML_RE = re.compile(r".*<.+>.*")


def validate_plain_text(value):
    if not isinstance(value, basestring):
        return
    if HTML_RE.match(value) is not None:
        raise ValidationError('HTML tags are not allowed')
