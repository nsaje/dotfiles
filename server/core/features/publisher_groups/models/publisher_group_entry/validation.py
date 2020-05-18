import utils.exc


def validate_placement(placement: str):  # typing (for mypy check)
    if placement == "":
        raise utils.exc.ValidationError("Placement must not be empty")

    if placement is not None and placement.strip().lower() == "not reported":
        raise utils.exc.ValidationError(f'Invalid placement: "{placement}"')
