from skywalking.profile.profile_status import ProfileStatusReference
from skywalking.profile.profile_task import ProfileTask
from skywalking.profile.profile_thread import ProfileThread
from skywalking.profile.thread_profiler import ThreadProfiler
from skywalking.trace.context import SpanContext
from skywalking.utils.integer import AtomicInteger
from skywalking.utils.array import AtomicArray

from concurrent.futures import ThreadPoolExecutor, Future
from threading import current_thread


class ProfileTaskExecutionContext:

    def __init__(self, task):
        self.task = task  # type: ProfileTask
        self._current_profiling_cnt = AtomicInteger(var=0)
        self._total_started_profiling_cnt = AtomicInteger(var=0)
        # TODO mini: config
        self.profiling_segment_slots = AtomicArray(length=5)
        self._profiling_future = None  # type: Future

    def start_profiling(self, executor_service: ThreadPoolExecutor):
        self._profiling_future = executor_service.submit(ProfileThread(self))

    def stop_profiling(self):
        if self._profiling_future is not None:
            self._profiling_future.cancel()

    def attempt_profiling(self, trace_context: SpanContext, segment_id: str, first_span_opname: str) -> ProfileStatusReference:
        """
        check have available slot to profile and add it
        """

        # check has available slot
        using_slot_cnt = self._current_profiling_cnt.get()
        # TODO mini: config.Profile.MAX_PARALLEL
        if using_slot_cnt >= 5:
            return ProfileStatusReference.create_with_none()

        # check first operation name matches
        if not self.task.first_span_op_name == first_span_opname:
            return ProfileStatusReference.create_with_none()

        # if out limit started profiling count then stop add profiling
        if self._total_started_profiling_cnt.get() > self.task.max_sampling_count:
            return ProfileStatusReference.create_with_none()

        # try to occupy slot
        if not self._current_profiling_cnt.compare_and_set(using_slot_cnt,
                                                           using_slot_cnt+1):
            return ProfileStatusReference.create_with_none()

        thread_profiler = ThreadProfiler(trace_context=trace_context,
                                         segment_id=segment_id,
                                         profiling_thread=current_thread(),
                                         profile_context=self)

        slot_length = self.profiling_segment_slots.length()
        for idx in range(slot_length):
            # occupy slot success
            if self.profiling_segment_slots.compare_and_set(idx, None, thread_profiler):
                return thread_profiler.profile_status

        return ProfileStatusReference.create_with_none()

    def stop_tracing_profile(self, trace_context: SpanContext):
        """
        find tracing context and clear on slot
        :param trace_context:
        :return:
        """

        # TODO:
        pass
