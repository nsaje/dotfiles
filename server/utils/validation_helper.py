import re

from django.core.exceptions import ValidationError

import utils.exc

HTML_RE = re.compile(r".*<.+>.*")
PLAIN_DOMAIN_RE = re.compile(r"^(?!\-)(?:[a-zA-Z\d\-]{0,62}[a-zA-Z\d]\.){1,126}(?!\d+)[a-zA-Z\d]{1,63}$")


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


def validate_domain_name(value):
    if not PLAIN_DOMAIN_RE.match(value):
        raise ValidationError("Invalid domain name")
