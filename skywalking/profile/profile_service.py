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

from concurrent.futures import ThreadPoolExecutor
from queue import Queue
from threading import Timer, RLock, Lock
from typing import Tuple

from skywalking import agent
from skywalking.loggings import logger, logger_debug_enabled
from skywalking.profile.profile_constants import ProfileConstants
from skywalking.profile.profile_context import ProfileTaskExecutionContext
from skywalking.profile.profile_status import ProfileStatusReference
from skywalking.profile.profile_task import ProfileTask
from skywalking.trace.context import SpanContext
from skywalking.utils.atomic_ref import AtomicRef
from skywalking.utils.time import current_milli_time


class Scheduler:

    @staticmethod
    def schedule(milliseconds, func, *args, **kwargs):
        seconds = milliseconds / 1000
        if seconds < 0:
            seconds = 0

        t = Timer(seconds, func, *args, **kwargs)
        t.daemon = True
        t.start()


class ProfileTaskExecutionService:
    MINUTE_TO_MILLIS = 60000

    def __init__(self):
        # Queue is thread safe
        self._profile_task_list = Queue()  # type: Queue
        # queue_lock for making sure complex operation of this profile_task_list is thread safe
        self.queue_lock = Lock()

        self._last_command_create_time = -1  # type: int
        # single thread executor
        self.profile_executor = ThreadPoolExecutor(max_workers=1)
        self.task_execution_context = AtomicRef(None)

        self.profile_task_scheduler = Scheduler()

        # rlock for process_profile_task and stop_current_profile_task
        self._rlock = RLock()

    def remove_from_profile_task_list(self, task: ProfileTask) -> bool:
        """
        Remove a task from profile_task_list in a thread safe state
        """
        with self.queue_lock:
            item_left = []
            result = False

            while not self._profile_task_list.empty():
                item = self._profile_task_list.get()
                if item == task:
                    result = True
                    # not put in item_list for removing it
                    continue

                item_left.append(item)

            for item in item_left:
                self._profile_task_list.put(item)

            return result

    def get_last_command_create_time(self) -> int:
        return self._last_command_create_time

    def add_profile_task(self, task: ProfileTask):
        # update last command create time, which will be used in command query
        if task.create_time > self._last_command_create_time:
            self._last_command_create_time = task.create_time

        # check profile task object
        success, error_reason = self._check_profile_task(task)
        if not success:
            logger.warning('check command error, cannot process this profile task. reason: %s', error_reason)
            return

        # add task to list
        self._profile_task_list.put(task)

        delay_millis = task.start_time - current_milli_time()
        # schedule to start task
        self.profile_task_scheduler.schedule(delay_millis, self.process_profile_task, [task])

    def add_profiling(self, context: SpanContext, segment_id: str, first_span_opname: str) -> ProfileStatusReference:
        execution_context = self.task_execution_context.get()  # type: ProfileTaskExecutionContext
        if execution_context is None:
            return ProfileStatusReference.create_with_none()

        return execution_context.attempt_profiling(context, segment_id, first_span_opname)

    def profiling_recheck(self, trace_context: SpanContext, segment_id: str, first_span_opname: str):
        """
        Re-check current trace need profiling, in case that third-party plugins change the operation name.
        """
        execution_context = self.task_execution_context.get()  # type: ProfileTaskExecutionContext
        if execution_context is None:
            return
        execution_context.profiling_recheck(trace_context, segment_id, first_span_opname)

    # using reentrant lock for process_profile_task and stop_current_profile_task,
    # to make sure thread safe.
    def process_profile_task(self, task: ProfileTask):
        with self._rlock:
            # make sure prev profile task already stopped
            self.stop_current_profile_task(self.task_execution_context.get())

            # make stop task schedule and task context
            current_context = ProfileTaskExecutionContext(task)
            self.task_execution_context.set(current_context)

            # start profiling this task
            current_context.start_profiling()
            if logger_debug_enabled:
                logger.debug('profile task [%s] for endpoint [%s] started', task.task_id, task.first_span_op_name)

            millis = task.duration * self.MINUTE_TO_MILLIS
            self.profile_task_scheduler.schedule(millis, self.stop_current_profile_task, [current_context])

    def stop_current_profile_task(self, need_stop: ProfileTaskExecutionContext):
        with self._rlock:
            # need_stop is None or task_execution_context is not need_stop context
            if need_stop is None or not self.task_execution_context.compare_and_set(need_stop, None):
                return

            need_stop.stop_profiling()
            if logger_debug_enabled:
                logger.debug('profile task [%s] for endpoint [%s] stopped', need_stop.task.task_id,
                             need_stop.task.first_span_op_name)

            self.remove_from_profile_task_list(need_stop.task)

            # notify profiling task has finished
            agent.notify_profile_finish(need_stop.task)

    def _check_profile_task(self, task: ProfileTask) -> Tuple[bool, str]:
        try:
            # endpoint name
            if len(task.first_span_op_name) == 0:
                return (False, f'endpoint name [{task.first_span_op_name}] error, '
                               f'should be str and not empty')
            # duration
            if task.duration < ProfileConstants.TASK_DURATION_MIN_MINUTE:
                return (False, f'monitor duration must be greater '
                               f'than {ProfileConstants.TASK_DURATION_MIN_MINUTE} minutes')
            if task.duration > ProfileConstants.TASK_DURATION_MAX_MINUTE:
                return (False, f'monitor duration must be less '
                               f'than {ProfileConstants.TASK_DURATION_MAX_MINUTE} minutes')
            # min duration threshold
            if task.min_duration_threshold < 0:
                return False, 'min duration threshold must be greater than or equals zero'

            # dump period
            if task.thread_dump_period < ProfileConstants.TASK_DUMP_PERIOD_MIN_MILLIS:
                return (False,
                        f'dump period must be greater than or equals to '
                        f'{ProfileConstants.TASK_DUMP_PERIOD_MIN_MILLIS} milliseconds')

            # max sampling count
            if task.max_sampling_count <= 0:
                return False, 'max sampling count must be greater than zero'
            if task.max_sampling_count >= ProfileConstants.TASK_MAX_SAMPLING_COUNT:
                return (False, f'max sampling count must be less than '
                               f'{ProfileConstants.TASK_MAX_SAMPLING_COUNT}')

            # check task queue
            task_finish_time = self._cal_profile_task_finish_time(task)

            # lock the self._profile_task_list.queue when check the item in it, avoid concurrency errors
            with self._profile_task_list.mutex:
                for profile_task in self._profile_task_list.queue:  # type: ProfileTask
                    # if the end time of the task to be added is during the execution of any data, means is a error data
                    if task.start_time <= task_finish_time <= self._cal_profile_task_finish_time(profile_task):
                        return (False,
                                f'there already have processing task in time range, '
                                f'could not add a new task again. processing task '
                                f'monitor endpoint name: {profile_task.first_span_op_name}')

            return True, ''

        except TypeError:
            return False, 'ProfileTask attributes have a type error'

    def _cal_profile_task_finish_time(self, task: ProfileTask) -> int:
        return task.start_time + task.duration * self.MINUTE_TO_MILLIS
