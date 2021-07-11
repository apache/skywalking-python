from skywalking.utils.lang import tostring


@tostring
class ProfileTask:

    def __init__(self,
                 task_id: str = None,
                 first_span_op_name: str = None,
                 duration: int = None,
                 min_duration_threshold: int = None,
                 thread_dump_period: int = None,
                 max_sampling_count: int = None,
                 start_time: int = None,
                 create_time: int = None):
        self.task_id = str(task_id)  # type: str
        self.first_span_op_name = str(first_span_op_name)  # type: str
        self.duration = int(duration)  # type: int
        self.min_duration_threshold = int(min_duration_threshold)  # type: int
        self.thread_dump_period = int(thread_dump_period)  # type: int
        self.max_sampling_count = int(max_sampling_count)  # type: int
        self.start_time = int(start_time)  # type: int
        self.create_time = int(create_time)  # type: int
