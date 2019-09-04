import signal
import threading
import time

import yappi


def _profile_signal_handler(signum, stack):
    if not is_running():
        start()
    else:
        stop_and_dump("live")


if threading.current_thread() is threading.main_thread():
    signal.signal(signal.SIGUSR2, _profile_signal_handler)


def is_running():
    return yappi.is_running()


def start():
    yappi.start()


def stop_and_dump(name=None):
    yappi.stop()
    stats = yappi.convert2pstats(yappi.get_func_stats())
    yappi.clear_stats()
    stats.sort_stats("cumtime")
    stats.print_stats()
    stats.dump_stats("%s-%s.pstats" % (name or "", str(int(time.time()))))
