import threading


class BaseThread(threading.Thread):
    def __init__(self, *args, **kwargs):
        self.parent = threading.current_thread()
        super(BaseThread, self).__init__(*args, **kwargs)
