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

from skywalking.protocol.common.Common_pb2 import Command

from skywalking.command.base_command import BaseCommand
from skywalking.utils.lang import tostring


@tostring
class ProfileTaskCommand(BaseCommand):
    NAME = 'ProfileTaskQuery'

    def __init__(self,
                 serial_number: str = '',
                 task_id: str = '',
                 endpoint_name: str = '',
                 duration: int = -1,
                 min_duration_threshold: int = -1,
                 dump_period: int = -1,
                 max_sampling_count: int = -1,
                 start_time: int = -1,
                 create_time: int = -1):

        BaseCommand.__init__(self, self.NAME, serial_number)

        self.task_id = task_id  # type: str
        self.endpoint_name = endpoint_name  # type: str
        self.duration = duration  # type: int
        self.min_duration_threshold = min_duration_threshold  # type: int
        self.dump_period = dump_period  # type: int
        self.max_sampling_count = max_sampling_count  # type: int
        self.start_time = start_time  # type: int
        self.create_time = create_time  # type: int

    @staticmethod
    def deserialize(command: Command):
        serial_number = None
        task_id = None
        endpoint_name = None
        duration = None
        min_duration_threshold = None
        dump_period = None
        max_sampling_count = None
        start_time = None
        create_time = None

        for pair in command.args:
            if pair.key == 'SerialNumber':
                serial_number = pair.value
            elif pair.key == 'EndpointName':
                endpoint_name = pair.value
            elif pair.key == 'TaskId':
                task_id = pair.value
            elif pair.key == 'Duration':
                duration = pair.value
            elif pair.key == 'MinDurationThreshold':
                min_duration_threshold = pair.value
            elif pair.key == 'DumpPeriod':
                dump_period = pair.value
            elif pair.key == 'MaxSamplingCount':
                max_sampling_count = pair.value
            elif pair.key == 'StartTime':
                start_time = pair.value
            elif pair.key == 'CreateTime':
                create_time = pair.value

        return ProfileTaskCommand(serial_number=serial_number, task_id=task_id,
                                  endpoint_name=endpoint_name, duration=duration,
                                  min_duration_threshold=min_duration_threshold, dump_period=dump_period,
                                  max_sampling_count=max_sampling_count, start_time=start_time,
                                  create_time=create_time)
