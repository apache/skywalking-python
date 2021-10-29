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

from typing import List

from skywalking.protocol.profile.Profile_pb2 import ThreadSnapshot, ThreadStack


class TracingThreadSnapshot:

    def __init__(self, task_id: str, trace_segment_id: str, sequence: int, time: int, stack_list: List[str]):
        self.task_id = task_id
        self.trace_segment_id = trace_segment_id
        self.sequence = sequence
        self.time = time
        self.stack_list = stack_list

    def transform(self) -> ThreadSnapshot:
        code_sigs = list(self.stack_list)
        stack = ThreadStack(codeSignatures=code_sigs)

        snapshot = ThreadSnapshot(
            taskId=str(self.task_id),
            traceSegmentId=str(self.trace_segment_id),
            time=int(self.time),
            sequence=int(self.sequence),
            stack=stack
        )

        return snapshot
