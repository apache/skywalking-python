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

link_vector = ['https://aioredis.readthedocs.io/']
support_matrix = {
    'aioredis': {
        '>=3.6': ['2.0.1']
    }
}
note = """"""


def install():
    from aioredis import Redis

    async def _sw_execute_command(self, op, *args, **kwargs):
        connargs = self.connection_pool.connection_kwargs
        peer = f'{connargs.get("host", "localhost")}:{connargs.get("port", 6379)}'

        context = get_context()
        with context.new_exit_span(op=f'Redis/AIORedis/{op}' or '/', peer=peer, component=Component.AIORedis) as span:
            span.layer = Layer.Cache

            span.tag(TagDbType('Redis'))
            span.tag(TagDbInstance(str(connargs.get('db', 0))))
            span.tag(TagDbStatement(op))

            return await _execute_command(self, op, *args, **kwargs)

    _execute_command = Redis.execute_command
    Redis.execute_command = _sw_execute_command


# Example code for someone who might want to make tests:
#
# async def aioredis_():
#     redis = aioredis.from_url("redis://localhost")
#     await redis.set("my-key", "value")
#     value = await redis.get("my-key")
#     print(value)
