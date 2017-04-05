from dash import constants


def get_human_value(target_os):
    name = constants.OperatingSystem.get_text(target_os['name'])

    if 'version' in target_os:
        if 'exact' in target_os['version']:
            return "{} ({})".format(
                name, constants.OperatingSystemVersion.get_text(target_os['version']['exact']))
        else:
            return "{} ({} - {})".format(
                name,
                constants.OperatingSystemVersion.get_text(target_os['version']['min']),
                constants.OperatingSystemVersion.get_text(target_os['version']['max'])
            )

    return name
