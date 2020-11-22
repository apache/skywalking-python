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
from skywalking.trace import tags
from skywalking.trace.context import get_context
from skywalking.trace.tags import Tag


def install():
    from redis.connection import Connection

    _send_command = Connection.send_command

    def _sw_send_command(this: Connection, *args, **kwargs):
        peer = "%s:%s" % (this.host, this.port)
        op = args[0]
        context = get_context()
        with context.new_exit_span(op="Redis/"+op or "/", peer=peer) as span:
            span.layer = Layer.Cache
            span.component = Component.Redis

            res = _send_command(this, *args, **kwargs)
            span.tag(Tag(key=tags.DbType, val="Redis"))
            span.tag(Tag(key=tags.DbInstance, val=this.db))
            span.tag(Tag(key=tags.DbStatement, val=op))

            return res

    Connection.send_command = _sw_send_command
