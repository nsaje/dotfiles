from dash import constants


def get_human_value_target_os(target_os):
    name = constants.OperatingSystem.get_text(target_os["name"])

    if "version" in target_os:
        version = target_os["version"]
        min_version = constants.OperatingSystemVersion.get_text(version.get("min"))
        max_version = constants.OperatingSystemVersion.get_text(version.get("max"))

        if min_version == max_version:
            return "{} ({})".format(name, min_version) if min_version else name

        if not min_version:
            return "{} ({} - {})".format(name, min_version, max_version)

    return name
