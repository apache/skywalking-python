from typing import List

from skywalking.protocol.profile.Profile_pb2 import ThreadSnapshot, ThreadStack


class TracingThreadSnapshot:

    def __init__(self, task_id: str, trace_segment_id: str, sequence: int, time: int, stack_list: List[str]):
        self.task_id = task_id
        self.trace_segment_id = trace_segment_id
        self.sequence = sequence
        self.time = time
        self.stack_list = stack_list

    def transform(self) -> ThreadSnapshot:
        snapshot = ThreadSnapshot(
            taskId=self.task_id,
            traceSegmentId=self.trace_segment_id,
            time=self.time,
            sequence=self.sequence,
            stack=ThreadStack(codeSignatures=[code_sign for code_sign in self.stack_list])
        )

        return snapshot
