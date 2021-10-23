#
# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

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
            raise IndexError('atomic array assignment index out of range')

        with self._lock:
            self._array[idx] = new_value

    def get(self, idx: int):
        if idx < 0 or idx >= self.length():
            raise IndexError('atomic array assignment index out of range')

        with self._lock:
            return self._array[idx]

    def compare_and_set(self, idx: int, expect, update) -> bool:
        """
        Atomically sets the value of array to the given updated value if the current value == the expected value
        :return: return True if success, False if the actual value was not equal to the expected value.
        """
        if idx < 0 or idx >= self.length():
            raise IndexError('atomic array assignment index out of range')

        with self._lock:
            if self._array[idx] == expect:
                self._array[idx] = update
                return True

            return False
