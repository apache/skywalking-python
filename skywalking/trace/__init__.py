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


class GlobalIdGenerator:
    """o
    Simplified snowflake algorithm that only rely on local distribution, fast alternative to uuid
    """

    # The PROCESS_ID must be regenerated upon fork to avoid collision
    PROCESS_ID = uuid.uuid1().hex  # uuid.UUID(int=random.getrandbits(128), version=4).hex

    @staticmethod
    def refresh_process_id():
        """
        Upon fork, a new processid will be given
        os.register_at_fork() does not consider uwsgi, so additional handling is done on the hook side
        This method is called from both agent.__init__.py and bootstrap.hooks.uwsgi_hook
        """
        GlobalIdGenerator.PROCESS_ID = uuid.uuid1().hex

    class IDContext:
        def __init__(self, last_timestamp, thread_seq):
            self.last_timestamp = last_timestamp
            self.thread_seq = thread_seq
            self.last_shift_timestamp = 0
            self.last_shift_value = 0

        def next_seq(self) -> int:
            """
            Concatenate timestamp(ms) and thread sequence to generate a unique id
            """
            return self.timestamp() * 10000 + self.next_thread_seq()

        def timestamp(self) -> int:
            """
            Simple solution to time shift back problems, originally implemented by Snoyflake
            """
            current_time_millis = time.perf_counter_ns() // 1_000_000
            if current_time_millis < self.last_timestamp:
                if self.last_shift_timestamp != current_time_millis:
                    self.last_shift_value += 1
                    self.last_shift_timestamp = current_time_millis
                return self.last_shift_value
            else:
                self.last_timestamp = current_time_millis
                return self.last_timestamp

        def next_thread_seq(self) -> int:
            """
            Generate sequence 0-9999 for the current thread
            """
            if self.thread_seq == 10000:
                self.thread_seq = 0
            return self.thread_seq

    THREAD_ID_SEQUENCE = threading.local()
    THREAD_ID_SEQUENCE.context = IDContext(time.perf_counter_ns() // 1_000_000, 0)

    @staticmethod
    def generate() -> str:
        """
        A fast alternative to uuid, only rely on local distribution
        """
        return f'{GlobalIdGenerator.PROCESS_ID}.{threading.get_ident()}.' \
               f'{GlobalIdGenerator.THREAD_ID_SEQUENCE.context.next_seq()}'


class ID(object):
    """
    This class is kept to maintain backward compatibility
    """
    def __init__(self, raw_id: str = None):
        if raw_id is None:
            self.value = GlobalIdGenerator.generate()
        else:
            self.value = raw_id

    def __str__(self):
        return self.value
