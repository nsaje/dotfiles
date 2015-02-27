import threading
import request_provider


class BaseThread(threading.Thread):
    def __init__(self, *args, **kwargs):
        self.parent = threading.current_thread()
        request_provider.mark_as_unsafe_to_delete()
        super(BaseThread, self).__init__(*args, **kwargs)
