import threading


class AtomicArray:

    def __init__(self, length: int):
        self._length = length
        self._array = [None] * self._length
        self._lock = threading.Lock()

    def __getitem__(self, idx):
        # for iteration
        with self._lock:
            return self._array[idx]

    def length(self) -> int:
        return self._length

    def set(self, idx: int, new_value):
        if idx < 0 or idx >= self.length():
            raise IndexError("atomic array assignment index out of range")

        with self._lock:
            self._array[idx] = new_value

    def get(self, idx: int):
        if idx < 0 or idx >= self.length():
            raise IndexError("atomic array assignment index out of range")

        with self._lock:
            return self._array[idx]

    def compare_and_set(self, idx: int, expect, update) -> bool:
        """
        Atomically sets the value of array to the given updated value if the current value == the expected value
        :return: return True if success, False if the actual value was not equal to the expected value.
        """
        if idx < 0 or idx >= self.length():
            raise IndexError("atomic array assignment index out of range")

        with self._lock:
            if self._array[idx] == expect:
                self._array[idx] = update
                return True

        return False
