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
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from skywalking.trace.context import SpanContext

from skywalking.trace import ID


class Snapshot:
    def __init__(
            self,
            segment_id: str = None,
            span_id: int = None,
            trace_id: ID = None,
            endpoint: str = None,
            correlation: dict = None
    ):
        self.trace_id = trace_id  # type: ID
        self.segment_id = segment_id  # type: str
        self.span_id = span_id  # type: int
        self.endpoint = endpoint  # type: str
        self.correlation = correlation.copy()  # type: dict

    def is_from_current(self, context: 'SpanContext'):
        return self.segment_id is not None and self.segment_id == context.capture().segment_id

    def is_valid(self):
        return self.segment_id is not None and self.span_id > -1 and self.trace_id is not None
