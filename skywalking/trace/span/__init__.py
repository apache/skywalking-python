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
import traceback
from abc import ABC
from copy import deepcopy
from typing import List
from typing import TYPE_CHECKING

from skywalking import Kind, Layer, Log, Component, LogItem, config
from skywalking.trace import ID
from skywalking.trace.carrier import Carrier
from skywalking.trace.segment import SegmentRef, Segment
from skywalking.trace.tags import Tag
from skywalking.utils.lang import tostring

if TYPE_CHECKING:
    from skywalking.trace.context import SpanContext


@tostring
class Span(ABC):
    def __init__(
            self,
            context: 'SpanContext',
            sid: int = -1,
            pid: int = -1,
            op: str = None,
            peer: str = None,
            kind: Kind = None,
            component: Component = None,
            layer: Layer = None,
    ):
        self.context = context  # type: SpanContext
        self.sid = sid  # type: int
        self.pid = pid  # type: int
        self.op = op  # type: str
        self.peer = peer  # type: str
        self.kind = kind  # type: Kind
        self.component = component or Component.Unknown  # type: Component
        self.layer = layer or Layer.Unknown  # type: Layer

        self.tags = []  # type: List[Tag]
        self.logs = []  # type: List[Log]
        self.refs = []  # type: List[SegmentRef]
        self.start_time = 0  # type: int
        self.end_time = 0  # type: int
        self.error_occurred = False  # type: bool

    def start(self):
        self.start_time = int(time.time() * 1000)
        self.context.start(self)

    def stop(self):
        return self.context.stop(self)

    def finish(self, segment: 'Segment') -> bool:
        self.end_time = int(time.time() * 1000)
        segment.archive(self)
        return True

    def raised(self) -> 'Span':
        self.error_occurred = True
        self.logs = [Log(items=[
            LogItem(key='Traceback', val=traceback.format_exc()),
        ])]
        return self

    def tag(self, tag: Tag) -> 'Span':
        if not tag.overridable:
            self.tags.append(deepcopy(tag))
            return self

        for t in self.tags:
            if t.key == tag.key:
                t.val = tag.val
                break

        return self

    def inject(self, carrier: 'Carrier') -> 'Span':
        raise RuntimeWarning(
            'can only inject context carrier into ExitSpan, this may be a potential bug in the agent, '
            'please report this in https://github.com/apache/skywalking/issues if you encounter this. '
        )

    def extract(self, carrier: 'Carrier') -> 'Span':
        if carrier is None:
            return self

        self.context.segment.relate(ID(carrier.trace_id))

        return self

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()
        if exc_tb is not None:
            return False
        return True


@tostring
class StackedSpan(Span):
    _depth = 0

    def finish(self, segment: 'Segment') -> bool:
        self._depth -= 1
        return self._depth == 0 and Span.finish(self, segment)


@tostring
class EntrySpan(StackedSpan):
    def __init__(
            self,
            context: 'SpanContext',
            sid: int = -1,
            pid: int = -1,
            op: str = None,
            peer: str = None,
            component: 'Component' = None,
            layer: 'Layer' = None,
    ):
        StackedSpan.__init__(
            self,
            context,
            sid,
            pid,
            op,
            peer,
            Kind.Entry,
            component,
            layer,
        )
        self._max_depth = 0

    def start(self):
        self._depth += 1
        self._max_depth = self._depth
        if self._max_depth == 1:
            StackedSpan.start(self)
        self.component = 0
        self.layer = Layer.Unknown
        self.logs = []
        self.tags = []

    def extract(self, carrier: 'Carrier') -> 'Span':
        Span.extract(self, carrier)

        if carrier is None:
            return self

        ref = SegmentRef(carrier=carrier)

        if ref not in self.refs:
            self.refs.append(ref)

        return self


@tostring
class ExitSpan(StackedSpan):
    def __init__(
            self,
            context: 'SpanContext',
            sid: int = -1,
            pid: int = -1,
            op: str = None,
            peer: str = None,
            component: 'Component' = None,
            layer: 'Layer' = None,
    ):
        StackedSpan.__init__(
            self,
            context,
            sid,
            pid,
            op,
            peer,
            Kind.Exit,
            component,
            layer,
        )

    def inject(self, carrier: 'Carrier') -> 'Span':
        carrier.trace_id = str(self.context.segment.related_traces[0])
        carrier.segment_id = str(self.context.segment.segment_id)
        carrier.span_id = self.sid
        carrier.service = config.service_name
        carrier.service_instance = config.service_instance
        carrier.endpoint = self.op
        carrier.client_address = self.peer
        return self

    def start(self):
        self._depth += 1
        StackedSpan.start(self)


@tostring
class NoopSpan(Span):
    def __init__(self, context: 'SpanContext' = None, kind: 'Kind' = None):
        Span.__init__(self, context=context, kind=kind)

    def inject(self, carrier: 'Carrier') -> 'Span':
        return self
