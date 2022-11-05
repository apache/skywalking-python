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

import sys
import time
import traceback

from packaging import version
from threading import Thread, Event, current_thread
from typing import Optional

from skywalking import agent
from skywalking import config
from skywalking import profile
from skywalking.loggings import logger
from skywalking.profile.profile_status import ProfileStatusReference, ProfileStatus
from skywalking.profile.profile_task import ProfileTask
from skywalking.profile.snapshot import TracingThreadSnapshot
from skywalking.trace.context import SpanContext
from skywalking.utils.array import AtomicArray
from skywalking.utils.integer import AtomicInteger
from skywalking.utils.time import current_milli_time


THREAD_MODEL = 'thread'
try:
    from gevent import monkey
    import greenlet
    from gevent.exceptions import BlockingSwitchOutError

    if monkey.is_module_patched('threading'):
        if version.parse(greenlet.__version__) <= version.parse('1.1.3.post0'):
            # todo: greenlet will raise a segment fault with signal 11 when it upgrade to 2.0.0
            # this issue may be caused by gevent's compatibility with greenlet
            # we should do some tests when gevent release a new version to verify if this issue would be fixed
            THREAD_MODEL = 'greenlet'
        else:
            logger.warn('greenlet profiler can not work with version >= 2.0.0')
except ImportError:
    pass


class ProfileTaskExecutionContext:
    def __init__(self, task: ProfileTask):
        self.task = task  # type: ProfileTask
        self._current_profiling_cnt = AtomicInteger(var=0)
        self._total_started_profiling_cnt = AtomicInteger(var=0)
        self.profiling_segment_slots = AtomicArray(length=config.profile_max_parallel)
        self._profiling_thread = None  # type: Optional[Thread]
        self._profiling_stop_event = None  # type: Optional[Event]

    def start_profiling(self):
        if THREAD_MODEL == 'greenlet':
            # GreenletProfiler will be started when it is created
            pass

        else:
            profile_thread = ProfileThread(self)
            self._profiling_stop_event = Event()

            self._profiling_thread = Thread(target=profile_thread.start, args=[self._profiling_stop_event], daemon=True)
            self._profiling_thread.start()

    def stop_profiling(self):
        if THREAD_MODEL == 'greenlet':
            for profiler in self.profiling_segment_slots:
                if profiler and isinstance(profiler, GreenletProfiler):
                    profiler.stop_profiling()

        else:
            if (
                self._profiling_thread is not None
                and self._profiling_stop_event is not None
            ):
                self._profiling_stop_event.set()

    def attempt_profiling(self, trace_context: SpanContext, segment_id: str, first_span_opname: str) -> \
            ProfileStatusReference:
        """
        check have available slot to profile and add it
        """

        # check has available slot
        using_slot_cnt = self._current_profiling_cnt.get()
        if using_slot_cnt >= config.profile_max_parallel:
            return ProfileStatusReference.create_with_none()

        # check first operation name matches
        if not self.task.first_span_op_name == first_span_opname:
            return ProfileStatusReference.create_with_none()

        # if out limit started profiling count then stop add profiling
        if self._total_started_profiling_cnt.get() > self.task.max_sampling_count:
            return ProfileStatusReference.create_with_none()

        # try to occupy slot
        if not self._current_profiling_cnt.compare_and_set(using_slot_cnt,
                                                           using_slot_cnt + 1):
            return ProfileStatusReference.create_with_none()

        if THREAD_MODEL == 'greenlet':
            curr = greenlet.getcurrent()
            thread_profiler = GreenletProfiler(
                trace_context=trace_context,
                segment_id=segment_id,
                profiling_thread=curr,
                profile_context=self,
            )
            thread_profiler.start_profiling(self)

        else:
            # default is thread
            thread_profiler = ThreadProfiler(
                trace_context=trace_context,
                segment_id=segment_id,
                profiling_thread=current_thread(),
                profile_context=self,
            )

        slot_length = self.profiling_segment_slots.length()
        for idx in range(slot_length):
            # occupy slot success
            if self.profiling_segment_slots.compare_and_set(idx, None, thread_profiler):
                return thread_profiler.profile_status

        return ProfileStatusReference.create_with_none()

    def profiling_recheck(self, trace_context: SpanContext, segment_id: str, first_span_opname: str):
        if trace_context.profile_status.is_being_watched():
            return

        # if first_span_opname was changed by other plugin, there can start profile as well
        trace_context.profile_status.update_status(self.attempt_profiling(trace_context,
                                                                          segment_id,
                                                                          first_span_opname).get())

    def stop_tracing_profile(self, trace_context: SpanContext):
        """
        find tracing context and clear on slot
        """
        for idx, profiler in enumerate(self.profiling_segment_slots):
            if profiler and profiler.matches(trace_context):
                self.profiling_segment_slots.set(idx, None)
                profiler.stop_profiling()
                self._current_profiling_cnt.add_and_get(-1)
                break

    def is_start_profileable(self):
        return self._total_started_profiling_cnt.add_and_get(1) <= self.task.max_sampling_count


class ProfileThread:
    def __init__(self, context: ProfileTaskExecutionContext):
        self._task_execution_context = context
        self._task_execution_service = profile.profile_task_execution_service
        self._stop_event = None  # type: Optional[Event]

    def start(self, stop_event: Event):
        self._stop_event = stop_event

        try:
            self.profiling(self._task_execution_context)
        except Exception as e:
            logger.error('profiling task fail. task_id:[%s] error:[%s]', self._task_execution_context.task.task_id, e)
        finally:
            self._task_execution_service.stop_current_profile_task(self._task_execution_context)

    def profiling(self, context: ProfileTaskExecutionContext):
        max_sleep_period = context.task.thread_dump_period

        while not self._stop_event.is_set():
            current_loop_start_time = current_milli_time()
            profilers = self._task_execution_context.profiling_segment_slots

            for profiler in profilers:  # type: ThreadProfiler
                if profiler is None or isinstance(profiler, GreenletProfiler):
                    continue
                if profiler.profile_status.get() is ProfileStatus.PENDING:
                    profiler.start_profiling_if_need()
                elif profiler.profile_status.get() is ProfileStatus.PROFILING:
                    snapshot = profiler.build_snapshot()
                    if snapshot is not None:
                        agent.add_profiling_snapshot(snapshot)
                    else:
                        # tell execution context current tracing thread dump failed, stop it
                        context.stop_tracing_profile(profiler.trace_context)

            need_sleep = (current_loop_start_time + max_sleep_period) - current_milli_time()
            if not need_sleep > 0:
                need_sleep = max_sleep_period

            # convert to float second
            time.sleep(need_sleep / 1000)


class ThreadProfiler:
    def __init__(self, trace_context: SpanContext, segment_id: str, profiling_thread: Thread,
                 profile_context: ProfileTaskExecutionContext):
        self.trace_context = trace_context
        self._segment_id = segment_id
        self._profiling_thread = profiling_thread
        self._profile_context = profile_context
        self._profile_start_time = -1
        self.profiling_max_time_mills = config.profile_duration * 60 * 1000

        self.dump_sequence = 0

        if trace_context.profile_status is None:
            self.profile_status = ProfileStatusReference.create_with_pending()
        else:
            self.profile_status = trace_context.profile_status  # type: ProfileStatusReference
            self.profile_status.update_status(ProfileStatus.PENDING)

    def start_profiling_if_need(self):
        if current_milli_time() - self.trace_context.create_time > self._profile_context.task.min_duration_threshold:
            self._profile_start_time = current_milli_time()
            self.trace_context.profile_status.update_status(ProfileStatus.PROFILING)

    def stop_profiling(self):
        self.trace_context.profile_status.update_status(ProfileStatus.STOPPED)

    def build_snapshot(self) -> Optional[TracingThreadSnapshot]:
        if not self._profiling_thread.is_alive():
            return None

        current_time = current_milli_time()

        stack_list = []

        # get thread stack of target thread
        stack = sys._current_frames().get(int(self._profiling_thread.ident))
        if not stack:
            return None

        extracted = traceback.extract_stack(stack)
        for idx, item in enumerate(extracted):
            if idx > config.profile_dump_max_stack_depth:
                break

            code_sig = f'{item.filename}.{item.name}: {item.lineno}'
            stack_list.append(code_sig)

        # if is first dump, check is can start profiling
        if self.dump_sequence == 0 and not self._profile_context.is_start_profileable():
            return None

        t = TracingThreadSnapshot(self._profile_context.task.task_id,
                                  self._segment_id,
                                  self.dump_sequence,
                                  current_time,
                                  stack_list)
        self.dump_sequence += 1
        return t

    def matches(self, trace_context: SpanContext) -> bool:
        return self.trace_context == trace_context


class GreenletProfiler:
    def __init__(
        self,
        trace_context: SpanContext,
        segment_id: str,
        profiling_thread,  # greenlet
        profile_context: ProfileTaskExecutionContext,
    ):
        self._task_execution_service = profile.profile_task_execution_service
        self.trace_context = trace_context
        self._segment_id = segment_id
        self._profiling_thread = profiling_thread
        self._profile_context = profile_context
        self._profile_start_time = -1
        self.profiling_max_time_mills = config.profile_duration * 60 * 1000

        self.dump_sequence = 0

        self.profile_status = ProfileStatusReference.create_with_pending()

    def stop_profiling(self):

        curr = self._profiling_thread
        curr.settrace(self._old_trace)
        self.profile_status.update_status(ProfileStatus.STOPPED)

    def build_snapshot(self) -> Optional[TracingThreadSnapshot]:
        stack_list = []
        extracted = traceback.extract_stack(self._profiling_thread.gr_frame)
        for idx, item in enumerate(extracted):
            if idx > config.profile_dump_max_stack_depth:
                break

            code_sig = f'{item.filename}.{item.name}: {item.lineno}'
            stack_list.append(code_sig)

        # if is first dump, check is can start profiling
        if (
            self.dump_sequence == 0
            and not self._profile_context.is_start_profileable()
        ):
            return None

        current_time = current_milli_time()
        snapshot = TracingThreadSnapshot(
            self._profile_context.task.task_id,
            self._segment_id,
            self.dump_sequence,
            current_time,
            stack_list,
                    )
        self.dump_sequence += 1
        return snapshot


    def start_profiling(self, context: ProfileTaskExecutionContext):
        self._task_execution_context = context
        try:
            curr = self._profiling_thread

            def callback(event, args):
                origin, target = args
                if origin == curr or target == curr:
                    try:
                        snapshot = self.build_snapshot()
                        if snapshot is not None:
                            agent.add_profiling_snapshot(snapshot)
                        else:
                            # tell execution context current tracing thread dump failed, stop it
                            # todo test it
                            self._profile_context.stop_tracing_profile(self.trace_context)
                    except BlockingSwitchOutError:
                        self._profile_context.stop_tracing_profile(self.trace_context)
                    except Exception as e:
                        logger.error(f'build and add snapshot failed. error: {e}')
                        self._profile_context.stop_tracing_profile(self.trace_context)
                        raise e


            self.profile_status.update_status(ProfileStatus.PROFILING)
            self._old_trace = curr.settrace(callback)

        except Exception as e:
            logger.error('profiling task fail. task_id:[%s] error:[%s]', self._profiling_context.task.task_id, e)
            # todo test this can current stop profile task or not
            self.profiling_context.stop_current_profile_task(
                self._task_execution_context
            )

    def matches(self, trace_context: SpanContext) -> bool:
        return self.trace_context == trace_context
