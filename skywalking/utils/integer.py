from skywalking.utils.atomic_ref import AtomicRef


class AtomicInteger(AtomicRef):
    def __init__(self, var: int):
        super().__init__(var)

    def add_and_get(self, delta: int):
        """
        Atomically adds the given value to the current value.

        :param delta: the value to add
        :return: the updated value
        """
        with self._lock:
            self._var += delta

        return self._var
