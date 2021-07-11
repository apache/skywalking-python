from skywalking.utils.lang import tostring
from skywalking.command.base_command import BaseCommand
from skywalking.protocol.common.Common_pb2 import Command


@tostring
class ProfileTaskCommand(BaseCommand):
    NAME = "ProfileTaskQuery"

    def __init__(self,
                 serial_number: str = None,
                 task_id: str = None,
                 endpoint_name: str = None,
                 duration: int = None,
                 min_duration_threshold: int = None,
                 dump_period: int = None,
                 max_sampling_count: int = None,
                 start_time: int = None,
                 create_time: int = None):

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
            if pair.key == "SerialNumber":
                serial_number = pair.value
            elif pair.key == "EndpointName":
                endpoint_name = pair.value
            elif pair.key == "TaskId":
                task_id = pair.value
            elif pair.key == "Duration":
                duration = pair.value
            elif pair.key == "MinDurationThreshold":
                min_duration_threshold = pair.value
            elif pair.key == "DumpPeriod":
                dump_period = pair.value
            elif pair.key == "MaxSamplingCount":
                max_sampling_count = pair.value
            elif pair.key == "StartTime":
                start_time = pair.value
            elif pair.key == "CreateTime":
                create_time = pair.value

        return ProfileTaskCommand(serial_number=serial_number, task_id=task_id,
                                  endpoint_name=endpoint_name, duration=duration,
                                  min_duration_threshold=min_duration_threshold, dump_period=dump_period,
                                  max_sampling_count=max_sampling_count, start_time=start_time,
                                  create_time=create_time)
