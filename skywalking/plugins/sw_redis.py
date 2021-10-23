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

from skywalking import Layer, Component
from skywalking.trace.context import get_context
from skywalking.trace.tags import TagDbType, TagDbInstance, TagDbStatement

link_vector = ['https://github.com/andymccurdy/redis-py/']
support_matrix = {
    'redis': {
        '>=3.6': ['3.5']  # "4.0" next, incompatible to current instrumentation
    }
}
note = """"""


def install():
    from redis.connection import Connection

    _send_command = Connection.send_command

    def _sw_send_command(this: Connection, *args, **kwargs):
        peer = f'{this.host}:{this.port}'
        op = args[0]
        context = get_context()
        with context.new_exit_span(op=f'Redis/{op}' or '/', peer=peer, component=Component.Redis) as span:
            span.layer = Layer.Cache

            res = _send_command(this, *args, **kwargs)
            span.tag(TagDbType('Redis'))
            span.tag(TagDbInstance(this.db))
            span.tag(TagDbStatement(op))

            return res

    Connection.send_command = _sw_send_command
