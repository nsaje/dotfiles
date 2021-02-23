import rest_framework.serializers

import dash.constants


def validate_ad_width(value):
    return _validate_ad_size(
        value,
        [s[0] for s in dash.constants.DisplayAdSize.get_all()],
        "Image width invalid. Supported widths are: {values}",
    )


def validate_ad_height(value):
    return _validate_ad_size(
        value,
        [s[1] for s in dash.constants.DisplayAdSize.get_all()],
        "Image height invalid. Supported heights are: {values}",
    )


def validate_ad_size_variants(width, height):
    if width is None and height is None:
        return
    supported_sizes = dash.constants.DisplayAdSize.get_all()
    if all(width != size[0] or height != size[1] for size in supported_sizes):
        sizes = ", ".join([str(s[0]) + "x" + str(s[1]) for s in supported_sizes])
        raise rest_framework.serializers.ValidationError(
            "Ad size invalid. Supported sizes are (width x height): {sizes}".format(sizes=sizes)
        )


def _validate_ad_size(value, supported_values, error_message):
    if value is None:
        return
    if all(value != width for width in supported_values):
        values = ", ".join([str(w) for w in supported_values])
        raise rest_framework.serializers.ValidationError([error_message.format(values=values)])
