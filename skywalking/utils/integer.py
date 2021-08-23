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
