import re

ID_RE = re.compile("/[0-9]+(/|$)")
UUID_RE = re.compile("/[a-fA-F0-9]{8}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{12}(/|$)")
FILE_RE = re.compile(".*[.][a-zA-Z]{3}$")
TOKEN_RE = re.compile("/[0-9a-zA-Z]+(-[0-9a-zA-Z]+)+(/|$)")


def clean_path(path):
    if FILE_RE.match(path):
        path = "_FILE_"
    path = ID_RE.sub("/_ID_\\1", path)
    path = UUID_RE.sub("/_UUID_\\1", path)
    path = TOKEN_RE.sub("/_TOKEN_\\2", path)
    return path
