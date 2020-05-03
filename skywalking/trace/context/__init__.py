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

import threading
from typing import List

from skywalking import agent
from skywalking.trace.segment import Segment
from skywalking.trace.span import Span, Kind, NoopSpan, EntrySpan, ExitSpan
from skywalking.utils.counter import Counter


class SpanContext(object):
    def __init__(self):
        self.spans: List[Span] = []
        self.segment: Segment = Segment()
        self._sid = Counter()

    def new_local_span(self, op: str) -> Span:
        parent: Span = self.spans[-1] if self.spans else None

        pid: int = parent.sid if parent else -1

        return Span(
            context=self,
            sid=self._sid.next(),
            pid=pid,
            op=op,
            kind=Kind.Local,
        )

    def new_entry_span(self, op: str) -> Span:
        parent: Span = self.spans[-1] if self.spans else None

        if parent is not None and parent.kind.is_entry:
            parent.op = op
            return parent

        pid: int = parent.sid if parent else -1

        return EntrySpan(
            context=self,
            sid=self._sid.next(),
            pid=pid,
            op=op,
        )

    def new_exit_span(self, op: str, peer: str) -> Span:
        parent: Span = self.spans[-1] if self.spans else None

        if parent is not None and parent.kind.is_exit:
            return parent

        pid: int = parent.sid if parent else -1

        return ExitSpan(
            context=self,
            sid=self._sid.next(),
            pid=pid,
            op=op,
            peer=peer,
        )

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


class NoopContext(SpanContext):
    def __init__(self):
        super().__init__()
        self._depth = 0
        self._noop_span = NoopSpan(self, kind=Kind.Local)

    def new_local_span(self, op: str) -> Span:
        self._depth += 1
        return self._noop_span

    def new_entry_span(self, op: str) -> Span:
        self._depth += 1
        return self._noop_span

    def new_exit_span(self, op: str, peer: str) -> Span:
        self._depth += 1
        return self._noop_span

    def stop(self, span: Span) -> bool:
        self._depth -= 1
        return self._depth == 0


_thread_local = threading.local()
_thread_local.context = None


def get_context(op: str = None) -> SpanContext:
    if _thread_local.context is not None:
        return _thread_local.context

    if not agent.connected() or not op or len(op.strip()) == 0:
        _thread_local.context = NoopContext()
    else:
        _thread_local.context = SpanContext()

    return _thread_local.context
