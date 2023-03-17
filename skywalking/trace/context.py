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
from typing import Optional

from skywalking import Component, config
from skywalking import profile
from skywalking.agent import agent
from skywalking.profile.profile_status import ProfileStatusReference
from skywalking.trace import ID
from skywalking.trace.carrier import Carrier
from skywalking.trace.segment import Segment, SegmentRef
from skywalking.trace.snapshot import Snapshot
from skywalking.trace.span import Span, Kind, NoopSpan, EntrySpan, ExitSpan
from skywalking.utils.counter import Counter
from skywalking.utils.exception import IllegalStateError
from skywalking.utils.time import current_milli_time

try:  # attempt to use async-local instead of thread-local context and spans
    import contextvars

    __spans = contextvars.ContextVar('spans')
    _spans = __spans.get
    _spans_set = __spans.set  # pyre-ignore

    def _spans():  # need to do this because can't set mutable default = [] in contextvars.ContextVar()
        spans = __spans.get(None)

        if spans is not None:
            return spans

        spans = []
        __spans.set(spans)

        return spans

    def _spans_dup():
        spans = __spans.get()[:]
        __spans.set(spans)

        return spans

    __spans.set([])

except ImportError:
    import threading

    class SwLocal(threading.local):
        def __init__(self):
            self.spans = []

    __local = SwLocal()

    def _spans():
        return __local.spans

    def _spans_set(spans):
        __local.spans = spans

    _spans_dup = _spans


class PrimaryEndpoint:
    """
    Behavior mocks Java agent's PrimaryEndpoint.
    Primary endpoint name is used for endpoint dependency. The name pick policy according to priority is
    1. Use the first entry span's operation name
    2. Use the first span's operation name
    """

    def __init__(self, span: Span):
        self.span: Span = span

    def set_primary_endpoint(self, span):
        if self.span.kind != Kind.Entry and span.kind == Kind.Entry:
            self.span = span

    def get_name(self):
        return self.span.op


class SpanContext:
    def __init__(self):
        self.segment: Segment = Segment()
        self._sid: Counter = Counter()
        self._correlation: dict = {}
        self._nspans: int = 0
        self.profile_status: Optional[ProfileStatusReference] = None
        self.create_time = current_milli_time()
        self.primary_endpoint: Optional[PrimaryEndpoint] = None

    @staticmethod
    def ignore_check(op: str, kind: Kind, carrier: Optional[Carrier] = None):
        if config.RE_IGNORE_PATH.match(op) or agent.is_segment_queue_full() or (carrier is not None and carrier.is_suppressed):
            return NoopSpan(context=NoopContext())

        return None

    def new_span(self, parent: Optional[Span], SpanType: type, **kwargs) -> Span:  # noqa
        finished = parent and not parent.depth
        context = SpanContext() if finished else self
        span = SpanType(context=context,
                        sid=context._sid.next(),
                        pid=parent.sid if parent and not finished else -1,
                        **kwargs)

        # if parent finished and segment was archived before this child starts then we need to refer to parent
        if finished:
            carrier = Carrier(
                trace_id=str(parent.context.segment.related_traces[0]),
                segment_id=str(parent.context.segment.segment_id),
                span_id=str(parent.sid),
                service=config.agent_name,
                service_instance=config.agent_instance_name,
                endpoint=parent.op,
                client_address=parent.peer,
                correlation=parent.context._correlation,
            )

            Span.extract(span, carrier)

        return span

    def new_local_span(self, op: str) -> Span:
        span = self.ignore_check(op, Kind.Local)
        if span is not None:
            return span

        parent = self.peek()
        return self.new_span(parent, Span, op=op, kind=Kind.Local)

    def new_entry_span(self, op: str, carrier: Optional[Carrier] = None, inherit: Optional[Component] = None) -> Span:
        span = self.ignore_check(op, Kind.Entry, carrier)
        if span is not None:
            return span

        parent = self.peek()
        # start profiling if profile_context is set
        if config.agent_profile_active and self.profile_status is None:
            self.profile_status = profile.profile_task_execution_service.add_profiling(self,
                                                                                       self.segment.segment_id,
                                                                                       op)

        if parent is not None and parent.kind.is_entry and inherit == parent.component:
            # Span's operation name could be overridden, recheck here
            # if the op name now is being profiling, start profile it here
            self.profiling_recheck(parent, op)

            span = parent
            span.op = op

        else:
            span = self.new_span(parent, EntrySpan, op=op)

            if carrier is not None and carrier.is_valid:  # TODO: should this be done irrespective of inheritance?
                span.extract(carrier=carrier)

        return span

    def new_exit_span(self, op: str, peer: str,
                      component: Optional[Component] = None, inherit: Optional[Component] = None) -> Span:
        span = self.ignore_check(op, Kind.Exit)
        if span is not None:
            return span

        parent = self.peek()
        if parent is not None and parent.kind.is_exit and component == parent.inherit:
            span = parent
            span.op = op
            span.peer = peer
            span.component = component

        else:
            span = self.new_span(parent, ExitSpan, op=op, peer=peer, component=component)

        if inherit:
            span.inherit = inherit

        return span

    def profiling_recheck(self, span: Span, op_name: str):
        if not config.agent_profile_active:
            return
        # only check first span, e.g, first opname is correct.
        if span.sid != 0:
            return
        profile.profile_task_execution_service.profiling_recheck(self, self.segment.segment_id, op_name)

    def start(self, span: Span):
        self._nspans += 1
        spans = _spans_dup()
        if span not in spans:
            spans.append(span)
            # check primary endpoint is set
            if not self.primary_endpoint:
                self.primary_endpoint = PrimaryEndpoint(span)
            else:
                self.primary_endpoint.set_primary_endpoint(span)

    def stop(self, span: Span) -> bool:
        spans = _spans_dup()
        span.finish(self.segment)

        try:
            spans.remove(span)
        except ValueError:
            pass

        self._nspans -= 1
        if self._nspans == 0:
            agent.archive_segment(self.segment)
            return True

        return False

    @staticmethod
    def peek() -> Optional[Span]:
        spans = _spans()
        return spans[-1] if spans else None

    @property
    def active_span(self):
        active_span = self.peek()
        if not active_span:
            raise IllegalStateError('No active span')
        return active_span

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
        spans = _spans()
        if len(spans) == 0:
            return None

        return Snapshot(
            segment_id=str(self.segment.segment_id),
            span_id=self.active_span.sid,
            trace_id=self.segment.related_traces[0],
            endpoint=spans[0].op,
            correlation=self._correlation,
        )

    def continued(self, snapshot: 'Snapshot'):
        if snapshot is None:
            return None
        if not snapshot.is_from_current(self) and snapshot.is_valid():
            ref = SegmentRef.build_ref(snapshot)
            span = self.active_span
            span.refs.append(ref)
            self.segment.relate(ID(ref.trace_id))
            self._correlation.update(snapshot.correlation)


class NoopContext(SpanContext):
    def __init__(self):
        super().__init__()

    def new_local_span(self, op: str) -> Span:
        return NoopSpan(self)

    def new_entry_span(self, op: str, carrier: Optional[Carrier] = None, inherit: Optional[Component] = None) -> Span:
        return NoopSpan(self)

    def new_exit_span(self, op: str, peer: str,
                      component: Optional[Component] = None, inherit: Optional[Component] = None) -> Span:
        return NoopSpan(self)

    def stop(self, span: Span) -> bool:
        spans = _spans_dup()

        try:
            spans.remove(span)
        except ValueError:
            pass

        self._nspans -= 1

        return self._nspans == 0

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


def get_context() -> SpanContext:
    spans = _spans()

    if spans:
        return spans[-1].context

    return SpanContext()
