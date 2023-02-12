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

from skywalking import Layer, Component, config
from skywalking.trace.context import get_context
from skywalking.trace.tags import TagDbType, TagDbInstance, TagDbStatement, TagDbSqlParameters

link_vector = ['https://github.com/MagicStack/asyncpg']
support_matrix = {
    'asyncpg': {
        '>=3.7': ['0.25.0'],
    }
}
note = """"""


def install():
    from asyncpg import Connection
    from asyncpg.protocol import Protocol

    def _sw_init(self, *args, **kwargs):
        _init(self, *args, **kwargs)
        self._protocol._addr = f'{self._addr[0]}:{self._addr[1]}'
        self._protocol._database = self._params.database

    async def __bind(proto, query, params, future, is_many=False):
        peer = getattr(proto, '_addr', '<unavailable>')  # just in case

        with get_context().new_exit_span(op='PostgreSQL/AsyncPG/bind', peer=peer,
                                         component=Component.AsyncPG) as span:
            span.layer = Layer.Database

            span.tag(TagDbType('PostgreSQL'))
            span.tag(TagDbInstance(getattr(proto, '_database', '<unavailable>')))
            span.tag(TagDbStatement(query))

            if config.plugin_sql_parameters_max_length and params is not None:
                if not is_many:
                    text = ','.join(str(v) for v in params)

                    if len(text) > config.plugin_sql_parameters_max_length:
                        text = f'{text[:config.plugin_sql_parameters_max_length]}...'

                    span.tag(TagDbSqlParameters(f'[{text}]'))

                else:
                    max_len = config.plugin_sql_parameters_max_length
                    total_len = 0
                    text_list = []

                    for _params in params:
                        text = f"[{','.join(str(v) for v in _params)}]"
                        total_len += len(text)

                        if total_len > max_len:
                            text_list.append(f'{text[:max_len - total_len]}...')

                            break

                        text_list.append(text)

                    span.tag(TagDbSqlParameters(f"[{','.join(text_list)}]"))

            return await future

    async def _sw_bind(proto, stmt, params, *args, **kwargs):
        return await __bind(proto, stmt.query, params, _bind(proto, stmt, params, *args, **kwargs))

    async def _sw_bind_execute(proto, stmt, params, *args, **kwargs):
        return await __bind(proto, stmt.query, params, _bind_execute(proto, stmt, params, *args, **kwargs))

    async def _sw_bind_execute_many(proto, stmt, params, *args, **kwargs):
        return await __bind(proto, stmt.query, params, _bind_execute_many(proto, stmt, params, *args, **kwargs), True)

    async def _sw_query(proto, query, *args, **kwargs):
        return await __bind(proto, query, (), _query(proto, query, *args, **kwargs))

    # async def _sw_execute(proto, stmt, *args, **kwargs):  # these may be useful in the future, left here for documentation purposes
    # async def _sw_prepare(*args, **kwargs):

    _init = Connection.__init__
    _bind = Protocol.bind
    _bind_execute = Protocol.bind_execute
    _bind_execute_many = Protocol.bind_execute_many
    _query = Protocol.query
    # _execute = Protocol.execute
    # _prepare = Protocol.prepare

    Connection.__init__ = _sw_init
    Protocol.bind = _sw_bind
    Protocol.bind_execute = _sw_bind_execute
    Protocol.bind_execute_many = _sw_bind_execute_many
    Protocol.query = _sw_query
    # Protocol.execute = _sw_execute
    # Protocol.prepare = _sw_prepare


# Example code for someone who might want to make tests:
#
# async def conncetAsycPg():
#     power=3
#     con = await asyncpg.connect(user='user',password='cv9493a32',database="db" , host='localhost')
#     await con.fetchval('SELECT 2 ^ $1', power)
#     types = await con.fetch('SELECT * FROM pg_type')
#     async with con.transaction():
#         async for record in con.cursor('SELECT generate_series(0, 100)'):
#             print(record)
#     await con.close()
