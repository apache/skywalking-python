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

import uuid
import threading
import time

from skywalking.utils.counter import AtomicCounter

# Fixme: seem to be useless?
_id = AtomicCounter()



class GlobalIdGenerator:
    PROCESS_ID = uuid.uuid1().hex  # uuid.UUID(int=random.getrandbits(128), version=4).hex


    class IDContext:
        def __init__(self, last_timestamp, thread_seq):
            self.last_timestamp = last_timestamp
            self.thread_seq = thread_seq
            self.last_shift_timestamp = 0
            self.last_shift_value = 0

        def next_seq(self):
            return self.timestamp() * 10000 + self.next_thread_seq()
            # return f'{self.timestamp() * 10000}{self.next_thread_seq()}'

        def timestamp(self):
            # current_time_millis = int(time.time() * 1000)
            # current_time_millis = time.time_ns() // 1_000_000
            current_time_millis = time.perf_counter_ns() // 1_000_000
            if current_time_millis < self.last_timestamp:
                if self.last_shift_timestamp != current_time_millis:
                    self.last_shift_value += 1
                    self.last_shift_timestamp = current_time_millis
                return self.last_shift_value
            else:
                self.last_timestamp = current_time_millis
                return self.last_timestamp

        def next_thread_seq(self):
            if self.thread_seq == 10000:
                self.thread_seq = 0
            return self.thread_seq

    THREAD_ID_SEQUENCE = threading.local()
    THREAD_ID_SEQUENCE.context = IDContext(time.perf_counter_ns() // 1_000_000, 0)

    @staticmethod
    def generate_fast():
        """ This is fastest by far faster than ID 4 times"""
        return f'{GlobalIdGenerator.PROCESS_ID}.{threading.get_ident()}.{GlobalIdGenerator.THREAD_ID_SEQUENCE.context.next_seq()}'

class ID(object):
    def __init__(self, raw_id: str = None):
        if raw_id is None:
            self.value = GlobalIdGenerator.generate_fast()
        else:
            self.value = raw_id

    def __str__(self):
        return self.value
