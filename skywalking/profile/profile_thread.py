from skywalking.profile.profile_status import ProfileStatus
from skywalking.profile.profile_task_execution_context import ProfileTaskExecutionContext

from skywalking.profile import profile_task_execution_service, add_profiling_snapshot
from skywalking.profile.profile_task_execution_context import ProfileTaskExecutionContext
from skywalking.loggings import logger
from threading import current_thread
import time

from skywalking.profile.thread_profiler import ThreadProfiler


class ProfileThread:

    def __init__(self, context: ProfileTaskExecutionContext):
        self._task_execution_context = context
        self._task_execution_service = profile_task_execution_service

    @staticmethod
    def current_milli_time() -> int:
        return round(time.time() * 1000)

    def start(self):
        try:
            self.profiling(self._task_execution_context)
        except Exception as e:
            logger.error("Profiling task fail. taskId:[%s] error:[%s]", self._task_execution_context.task.task_id, e)
        finally:
            self._task_execution_service.stop_current_profile_task(self._task_execution_context)

    def profiling(self, context: ProfileTaskExecutionContext):
        max_sleep_period = context.task.thread_dump_period
        current_loop_start_time = -1

        while current_thread().is_alive():
            current_loop_start_time = self.current_milli_time()
            profilers = self._task_execution_context.profiling_segment_slots

            for profiler in profilers:  # type: ThreadProfiler
                if profiler is None:
                    continue

                if profiler.profile_status.get() is ProfileStatus.PENDING:
                    profiler.start_profiling_if_need()
                    break
                elif profiler.profile_status.get() is ProfileStatus.PROFILING:
                    snapshot = profiler.build_snapshot()

                    if snapshot is not None:
                        add_profiling_snapshot(snapshot)
                    else:
                        # tell execution context current tracing thread dump failed, stop it
                        context.stop_tracing_profile(profiler.trace_context)

                    break

        need_sleep = (current_loop_start_time + max_sleep_period) - self.current_milli_time()
        if not need_sleep > 0:
            need_sleep = max_sleep_period

        # convert to float sec
        time.sleep(need_sleep/1000)
