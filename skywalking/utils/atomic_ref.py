import threading


class AtomicRef:
    def __init__(self, var):
        self._lock = threading.Lock()
        self._var = var

    def get(self):
        with self._lock:
            return self._var

    def set(self, new_var):
        with self._lock:
            self._var = new_var

    def compare_and_set(self, expect, update) -> bool:
        """
        Atomically sets the value to the given updated value if the current value == the expected value

        :return: return True if success, False if the actual value was not equal to the expected value.
        """
        with self._lock:
            if self._var == expect:
                self._var = update
                return True

        return False





