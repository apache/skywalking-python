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

from skywalking import Component, agent, config
from skywalking import profile
from skywalking.agent import isfull
from skywalking.profile.profile_status import ProfileStatusReference
from skywalking.trace import ID
from skywalking.trace.carrier import Carrier
from skywalking.trace.segment import Segment, SegmentRef
from skywalking.trace.snapshot import Snapshot
from skywalking.trace.span import Span, Kind, NoopSpan, EntrySpan, ExitSpan
from skywalking.utils.counter import Counter
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


class SpanContext(object):
    def __init__(self):
        self.segment = Segment()  # type: Segment
        self._sid = Counter()
        self._correlation = {}  # type: dict
        self._nspans = 0
        self.profile_status = None  # type: ProfileStatusReference
        self.create_time = current_milli_time()

    def ignore_check(self, op: str, kind: Kind, carrier: 'Carrier' = None):
        if config.RE_IGNORE_PATH.match(op) or isfull() or (carrier is not None and carrier.is_suppressed):
            return NoopSpan(context=NoopContext())

        return None

    def new_span(self, parent: Span, SpanType: type, **kwargs) -> Span: # noqa
        finished = parent and not parent._depth
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
                service=config.service_name,
                service_instance=config.service_instance,
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

        spans = _spans()
        parent = spans[-1] if spans else None  # type: Span

        return self.new_span(parent, Span, op=op, kind=Kind.Local)

    def new_entry_span(self, op: str, carrier: 'Carrier' = None, inherit: Component = None) -> Span:
        span = self.ignore_check(op, Kind.Entry, carrier)
        if span is not None:
            return span

        spans = _spans()
        parent = spans[-1] if spans else None  # type: Span

        # start profiling if profile_context is set
        if self.profile_status is None:
            self.profile_status = profile.profile_task_execution_service.add_profiling(self,
                                                                                       self.segment.segment_id,
                                                                                       op)

        if parent is not None and parent.kind.is_entry and inherit == parent.component:
            # Span's operation name could be override, recheck here
            # if the op name now is being profiling, start profile it here
            self.profiling_recheck(parent, op)

            span = parent
            span.op = op

        else:
            span = self.new_span(parent, EntrySpan, op=op)

            if carrier is not None and carrier.is_valid:  # TODO: should this be done irrespective of inheritance?
                span.extract(carrier=carrier)

        return span

    def new_exit_span(self, op: str, peer: str, component: Component = None, inherit: Component = None) -> Span:
        span = self.ignore_check(op, Kind.Exit)
        if span is not None:
            return span

        spans = _spans()
        parent = spans[-1] if spans else None  # type: Span

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
        # only check first span, e.g, first opname is correct.
        if span.sid != 0:
            return
        profile.profile_task_execution_service.profiling_recheck(self, self.segment.segment_id, op_name)

    def start(self, span: Span):
        self._nspans += 1
        spans = _spans_dup()
        if span not in spans:
            spans.append(span)

    def stop(self, span: Span) -> bool:
        spans = _spans_dup()
        span.finish(self.segment)

        try:
            spans.remove(span)
        except Exception:
            pass

        self._nspans -= 1
        if self._nspans == 0:
            agent.archive(self.segment)
            return True

        return False

    def active_span(self):
        spans = _spans()
        if spans:
            return spans[len(spans) - 1]

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
        spans = _spans()
        if len(spans) == 0:
            return None

        return Snapshot(
            segment_id=str(self.segment.segment_id),
            span_id=self.active_span().sid,
            trace_id=self.segment.related_traces[0],
            endpoint=spans[0].op,
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

    def new_local_span(self, op: str) -> Span:
        return NoopSpan(self)

    def new_entry_span(self, op: str, carrier: 'Carrier' = None, inherit: Component = None) -> Span:
        return NoopSpan(self)

    def new_exit_span(self, op: str, peer: str, component: Component = None, inherit: Component = None) -> Span:
        return NoopSpan(self)

    def stop(self, span: Span) -> bool:
        spans = _spans_dup()

        try:
            spans.remove(span)
        except Exception:
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
        return spans[len(spans) - 1].context

    return SpanContext()
