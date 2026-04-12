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

from skywalking.trace.context import get_context

link_vector = ['https://docs.python.org/3/library/threading.html']
support_matrix = {
    'threading': {
        '>=3.7': ['*']
    }
}
note = """Automatically propagates trace context across threads."""


def install():
    _original_init = threading.Thread.__init__
    _original_run = threading.Thread.run

    def _sw_init(self, *args, **kwargs):
        _original_init(self, *args, **kwargs)
        self._sw_snapshot = get_context().capture()

    def _sw_run(self):
        snapshot = getattr(self, '_sw_snapshot', None)
        target = getattr(self, '_target', None)

        # If target is @runnable-wrapped, let @runnable handle the span and continued
        if snapshot is not None and not getattr(target, '_sw_runnable', False):
            context = get_context()
            op = f'Thread/{target.__name__}' if target and hasattr(target, '__name__') else f'Thread/{self.name}'
            with context.new_local_span(op=op):
                context.continued(snapshot)
                _original_run(self)
        else:
            _original_run(self)

    threading.Thread.__init__ = _sw_init
    threading.Thread.run = _sw_run
