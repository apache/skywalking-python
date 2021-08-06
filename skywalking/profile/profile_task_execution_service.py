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

from queue import Queue
from skywalking.loggings import logger
from skywalking.profile.profile_constants import ProfileConstants
from skywalking.profile.profile_task import ProfileTask


class ProfileTaskExecutionService:
    MINUTE_TO_MILLIS = 60000

    def __init__(self):
        # Queue is thread safe
        self.__profile_task_list = Queue()  # type: Queue
        self.__last_command_create_time = -1  # type: int

    def get_last_command_create_time(self) -> int:
        return self.__last_command_create_time

    def add_profile_task(self, task: ProfileTask):
        # update last command create time, which will be used in command query
        if task.create_time > self.__last_command_create_time:
            self.__last_command_create_time = task.create_time

        # check profile task object
        result = self.__check_profile_task(task)
        if not result.success:
            logger.warning("check command error, cannot process this profile task. reason: %s", result.error_reason)
            return

        # add task to list
        self.__profile_task_list.put(task)

    class CheckResult:
        def __init__(self, success: bool, error_reason: str):
            self.success = success  # type: bool
            self.error_reason = error_reason  # type: str

    def __check_profile_task(self, task: ProfileTask) -> CheckResult:
        try:
            # endpoint name
            if len(task.first_span_op_name) == 0:
                return self.CheckResult(False, "endpoint name [{}] error, "
                                               "should be str and not empty".format(task.first_span_op_name))
            # duration
            if task.duration < ProfileConstants.TASK_DURATION_MIN_MINUTE:
                return self.CheckResult(False, "monitor duration must greater"
                                               " than {} minutes".format(ProfileConstants.TASK_DURATION_MIN_MINUTE))
            if task.duration > ProfileConstants.TASK_DURATION_MAX_MINUTE:
                return self.CheckResult(False, "monitor duration must less"
                                               " than {} minutes".format(ProfileConstants.TASK_DURATION_MAX_MINUTE))
            # min duration threshold
            if task.min_duration_threshold < 0:
                return self.CheckResult(False, "min duration threshold must greater than or equals zero")

            # dump period
            if task.thread_dump_period < ProfileConstants.TASK_DUMP_PERIOD_MIN_MILLIS:
                return self.CheckResult(False, "dump period must be greater than or equals to {}"
                                               " milliseconds".format(ProfileConstants.TASK_DUMP_PERIOD_MIN_MILLIS))

            # max sampling count
            if task.max_sampling_count <= 0:
                return self.CheckResult(False, "max sampling count must greater than zero")
            if task.max_sampling_count >= ProfileConstants.TASK_MAX_SAMPLING_COUNT:
                return self.CheckResult(False, "max sampling count must less"
                                               " than {}".format(ProfileConstants.TASK_MAX_SAMPLING_COUNT))

            # check task queue
            task_finish_time = self.__cal_profile_task_finish_time(task)

            # lock the self.__profile_task_list.queue when check the item in it, avoid concurrency errors
            with self.__profile_task_list.mutex:
                for profile_task in self.__profile_task_list.queue:  # type: ProfileTask
                    # if the end time of the task to be added is during the execution of any data, means is a error data
                    if task.start_time <= task_finish_time <= self.__cal_profile_task_finish_time(profile_task):
                        return self.CheckResult(False, "there already have processing task in time range, "
                                                       "could not add a new task again. processing task monitor "
                                                       "endpoint name: {}".format(profile_task.first_span_op_name))

            return self.CheckResult(True, "")

        except TypeError:
            return self.CheckResult(False, "ProfileTask attributes has type error")

    def __cal_profile_task_finish_time(self, task: ProfileTask) -> int:
        return task.start_time + task.duration * self.MINUTE_TO_MILLIS
