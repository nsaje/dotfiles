import re

import djangorestframework_camel_case.util

camelize_re = re.compile(r"[a-zA-Z0-9]?(_[a-z0-9])")


def camel_to_snake(string):
    return djangorestframework_camel_case.util.camel_to_underscore(string)


def snake_to_camel(string):
    m = camelize_re.search(string)
    while m:
        st = m.start(1)
        string = string[:st] + string[st + 1].upper() + string[st + 2 :]
        m = camelize_re.search(string)
    return string
