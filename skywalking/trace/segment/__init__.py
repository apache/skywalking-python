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

import time
from typing import List, TYPE_CHECKING

from skywalking.trace import ID
from skywalking.utils.lang import tostring

if TYPE_CHECKING:
    from skywalking.trace.carrier import Carrier
    from skywalking.trace.span import Span


class SegmentRef(object):
    def __init__(self, carrier: 'Carrier'):
        self.ref_type = 'CrossProcess'  # type: str
        self.trace_id = carrier.trace_id  # type: str
        self.segment_id = carrier.segment_id  # type: str
        self.span_id = carrier.span_id  # type: int
        self.service = carrier.service  # type: str
        self.service_instance = carrier.service_instance  # type: str
        self.endpoint = carrier.endpoint  # type: str
        self.client_address = carrier.client_address  # type: str


class _NewID(ID):
    pass


@tostring
class Segment(object):
    def __init__(self):
        self.segment_id = ID()  # type: ID
        self.spans = []  # type: List[Span]
        self.timestamp = int(time.time() * 1000)  # type: int
        self.related_traces = [_NewID()]  # type: List[ID]

    def archive(self, span: 'Span'):
        self.spans.append(span)

    def relate(self, trace_id: ID):
        if isinstance(self.related_traces[0], _NewID):
            del self.related_traces[-1]
        self.related_traces.append(trace_id)
