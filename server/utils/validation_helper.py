import re

from django.core.exceptions import ValidationError
import utils.exc

HTML_RE = re.compile(r".*<.+>.*")


def validate_plain_text(value):
    if not isinstance(value, str):
        return
    if HTML_RE.match(value) is not None:
        raise ValidationError("HTML tags are not allowed")


def validate_multiple(*validators, changes=None):
    errors = []
    for v in validators:
        try:
            if changes is not None:
                v(changes)
            else:
                v()
        except Exception as e:
            errors.append(e)
    if errors:
        raise utils.exc.MultipleValidationError(errors=errors)
