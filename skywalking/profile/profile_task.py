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

from skywalking.utils.lang import tostring


@tostring
class ProfileTask:

    def __init__(self,
                 task_id: str = '',
                 first_span_op_name: str = '',
                 duration: int = -1,
                 min_duration_threshold: int = -1,
                 thread_dump_period: int = -1,
                 max_sampling_count: int = -1,
                 start_time: int = -1,
                 create_time: int = -1):
        self.task_id = str(task_id)  # type: str
        self.first_span_op_name = str(first_span_op_name)  # type: str
        self.duration = int(duration)  # type: int
        # when can start profile after span context created
        self.min_duration_threshold = int(min_duration_threshold)  # type: int
        # profile interval
        self.thread_dump_period = int(thread_dump_period)  # type: int
        self.max_sampling_count = int(max_sampling_count)  # type: int
        self.start_time = int(start_time)  # type: int
        self.create_time = int(create_time)  # type: int
