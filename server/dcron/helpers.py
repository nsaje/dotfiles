def get_command(argv):
    command, _ = get_command_and_arguments(argv)
    return command


def get_arguments(argv):
    _, arguments = get_command_and_arguments(argv)
    return arguments


def get_command_and_arguments(argv):
    if len(argv) < 2:
        raise ValueError("Illegal arguments: %s" % argv)

    if "manage.py" not in argv[0]:
        raise ValueError("Not a management command: %s" % argv)

    if argv[1] == "dcron_launcher":
        command = argv[2]
        arguments = argv[3:]
    else:
        command = argv[1]
        arguments = argv[2:]

    return command, arguments
