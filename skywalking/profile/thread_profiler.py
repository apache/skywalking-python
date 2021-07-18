from skywalking.profile.tracing_thread_snapshot import TracingThreadSnapshot
from skywalking.profile.profile_status import ProfileStatusReference, ProfileStatus
from skywalking.profile.profile_task_execution_context import ProfileTaskExecutionContext
from skywalking.trace.context import SpanContext
from threading import Thread
from threading import current_thread


class ThreadProfiler:
    def __init__(self, trace_context: SpanContext, segment_id: str, profiling_thread: Thread,
                 profile_context: ProfileTaskExecutionContext):
        self.trace_context = trace_context
        self._segment_id = segment_id
        self._profiling_thread = profiling_thread
        self._profile_context = profile_context

        if trace_context.profile_status is None:
            self.profile_status = ProfileStatusReference.create_with_pending()
        else:
            self.profile_status = trace_context.profile_status  # type: ProfileStatusReference
            self.profile_status.update_status(ProfileStatus.PENDING)

        # TODO: Config.Profile.MAX_DURATION
        self.profiling_max_time_mills = 10*60*1000

    def start_profiling_if_need(self):
        # TODO
        pass

    def stop_profiling(self):
        # TODO
        pass

    def build_snapshot(self) -> TracingThreadSnapshot:
        # TODO
        pass

