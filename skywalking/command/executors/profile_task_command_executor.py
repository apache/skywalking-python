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

from skywalking.command.executors.command_executor import CommandExecutor
from skywalking.command.profile_task_command import ProfileTaskCommand
from skywalking import profile
from skywalking.profile.profile_task import ProfileTask


class ProfileTaskCommandExecutor(CommandExecutor):

    def execute(self, command: ProfileTaskCommand):
        profile_task = ProfileTask(task_id=command.task_id,
                                   first_span_op_name=command.endpoint_name,
                                   duration=command.duration,
                                   min_duration_threshold=command.min_duration_threshold,
                                   thread_dump_period=command.dump_period,
                                   max_sampling_count=command.max_sampling_count,
                                   start_time=command.start_time,
                                   create_time=command.create_time)

        profile.profile_task_execution_service.add_profile_task(profile_task)
