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

import logging
import threading
from typing import List

from skywalking import agent, config
from skywalking.trace import ID
from skywalking.trace.carrier import Carrier
from skywalking.trace.segment import Segment, SegmentRef
from skywalking.trace.snapshot import Snapshot
from skywalking.trace.span import Span, Kind, NoopSpan, EntrySpan, ExitSpan
from skywalking.utils.ant_matcher import fast_path_match
from skywalking.utils.counter import Counter

logger = logging.getLogger(__name__)


class SpanContext(object):
    def __init__(self):
        self.spans = []  # type: List[Span]
        self.segment = Segment()  # type: Segment
        self._sid = Counter()
        self._correlation = {}  # type: dict

    def new_local_span(self, op: str) -> Span:
        span = self.ignore_check(op, Kind.Local)
        if span is not None:
            return span

        parent = self.spans[-1] if self.spans else None  # type: Span

        return Span(
            context=self,
            sid=self._sid.next(),
            pid=parent.sid if parent else -1,
            op=op,
            kind=Kind.Local,
        )

    def new_entry_span(self, op: str, carrier: 'Carrier' = None) -> Span:
        span = self.ignore_check(op, Kind.Entry)
        if span is not None:
            return span

        parent = self.spans[-1] if self.spans else None  # type: Span

        span = parent if parent is not None and parent.kind.is_entry else EntrySpan(
            context=self,
            sid=self._sid.next(),
            pid=parent.sid if parent else -1,
        )
        span.op = op

        if carrier is not None and carrier.is_valid:
            span.extract(carrier=carrier)

        return span

    def new_exit_span(self, op: str, peer: str, carrier: 'Carrier' = None) -> Span:
        span = self.ignore_check(op, Kind.Exit)
        if span is not None:
            return span

        parent = self.spans[-1] if self.spans else None  # type: Span

        span = parent if parent is not None and parent.kind.is_exit else ExitSpan(
            context=self,
            sid=self._sid.next(),
            pid=parent.sid if parent else -1,
            op=op,
            peer=peer,
        )

        if carrier is not None:
            span.inject(carrier=carrier)

        return span

    def ignore_check(self, op: str, kind: Kind):
        suffix_idx = op.rfind(".")
        if suffix_idx > -1 and config.ignore_suffix.find(op[suffix_idx:]) > -1:
            return NoopSpan(
                context=NoopContext(),
                kind=kind,
            )
        if config.trace_ignore:
            for pattern in config.trace_ignore_path:
                if fast_path_match(pattern, op):
                    return NoopSpan(
                        context=NoopContext(),
                        kind=kind,
                    )

        return None

    def start(self, span: Span):
        if span not in self.spans:
            self.spans.append(span)

    def stop(self, span: Span) -> bool:
        assert span is self.spans[-1]

        span.finish(self.segment) and self.spans.pop()

        if len(self.spans) == 0:
            _thread_local.context = None
            agent.archive(self.segment)

        return len(self.spans) == 0

    def active_span(self):
        if self.spans:
            return self.spans[len(self.spans) - 1]

        return None

    def get_correlation(self, key):
        if key in self._correlation:
            return self._correlation[key]
        return None

    def put_correlation(self, key, value):
        if key is None:
            return
        if value is None:
            self._correlation.pop(key, value)
            return
        if len(value) > config.correlation_value_max_length:
            return
        if len(self._correlation) > config.correlation_element_max_number:
            return

        self._correlation[key] = value

    def capture(self):
        if len(self.spans) == 0:
            return None

        return Snapshot(
            segment_id=str(self.segment.segment_id),
            span_id=self.active_span().sid,
            trace_id=self.segment.related_traces[0],
            endpoint=self.spans[0].op,
            correlation=self._correlation,
        )

    def continued(self, snapshot: 'Snapshot'):
        if snapshot is None:
            return None
        if not snapshot.is_from_current(self) and snapshot.is_valid():
            ref = SegmentRef.build_ref(snapshot)
            span = self.active_span()
            span.refs.append(ref)
            self.segment.relate(ID(ref.trace_id))
            self._correlation.update(snapshot.correlation)


class NoopContext(SpanContext):
    def __init__(self):
        super().__init__()
        self._depth = 0
        self._noop_span = NoopSpan(self, kind=Kind.Local)
        self.correlation = {}  # type: dict

    def new_local_span(self, op: str) -> Span:
        self._depth += 1
        return self._noop_span

    def new_entry_span(self, op: str, carrier: 'Carrier' = None) -> Span:
        self._depth += 1
        if carrier is not None:
            self._noop_span.extract(carrier)
        return self._noop_span

    def new_exit_span(self, op: str, peer: str, carrier: 'Carrier' = None) -> Span:
        self._depth += 1
        if carrier is not None:
            self._noop_span.inject(carrier)

        return self._noop_span

    def stop(self, span: Span) -> bool:
        self._depth -= 1
        return self._depth == 0

    def active_span(self):
        return self._noop_span

    def capture(self):
        return Snapshot(
            segment_id=None,
            span_id=-1,
            trace_id=None,
            endpoint=None,
            correlation=self._correlation,
        )

    def continued(self, snapshot: 'Snapshot'):
        self._correlation.update(snapshot.correlation)


_thread_local = threading.local()
_thread_local.context = None


def get_context() -> SpanContext:
    if not hasattr(_thread_local, 'context'):
        _thread_local.context = None
    _thread_local.context = _thread_local.context or (SpanContext() if agent.connected() else NoopContext())

    return _thread_local.context
