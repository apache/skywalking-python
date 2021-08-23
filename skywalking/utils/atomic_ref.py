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
