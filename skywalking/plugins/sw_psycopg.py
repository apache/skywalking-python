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

link_vector = ['https://www.psycopg.org/']
support_matrix = {
    'psycopg[binary]': {
        '>=3.6': ['3.0']  # psycopg is psycopg3
    }
}
note = """"""


def install_sync():
    import wrapt  # psycopg is read-only C extension objects so they need to be proxied
    import psycopg

    # synchronous

    class ProxyCursor(wrapt.ObjectProxy):
        def __init__(self, cur):
            wrapt.ObjectProxy.__init__(self, cur)

            self._self_cur = cur

        def __enter__(self):
            return ProxyCursor(wrapt.ObjectProxy.__enter__(self))

        def execute(self, query, vars=None, *args, **kwargs):
            dsn = self.connection.info.get_parameters()
            port = self.connection.info.port
            peer = f"{dsn['host']}:{str(port)}"

            with get_context().new_exit_span(op='PostgreSLQ/Psycopg/execute', peer=peer,
                                             component=Component.Psycopg) as span:
                span.layer = Layer.Database

                span.tag(TagDbType('PostgreSQL'))
                span.tag(TagDbInstance(dsn['dbname']))
                span.tag(TagDbStatement(query))

                if config.sql_parameters_length and vars is not None:
                    text = ','.join(str(v) for v in vars)

                    if len(text) > config.sql_parameters_length:
                        text = f'{text[:config.sql_parameters_length]}...'

                    span.tag(TagDbSqlParameters(f'[{text}]'))

                return self._self_cur.execute(query, vars, *args, **kwargs)

        def executemany(self, query, vars_list, *args, **kwargs):
            dsn = self.connection.info.get_parameters()
            port = self.connection.info.port
            peer = f"{dsn['host']}:{str(port)}"

            with get_context().new_exit_span(op='PostgreSLQ/Psycopg/executemany', peer=peer,
                                             component=Component.Psycopg) as span:
                span.layer = Layer.Database

                span.tag(TagDbType('PostgreSQL'))
                span.tag(TagDbInstance(dsn['dbname']))
                span.tag(TagDbStatement(query))

                if config.sql_parameters_length:
                    max_len = config.sql_parameters_length
                    total_len = 0
                    text_list = []

                    for vars in vars_list:
                        text = f"[{','.join(str(v) for v in vars)}]"
                        total_len += len(text)

                        if total_len > max_len:
                            text_list.append(f'{text[:max_len - total_len]}...')

                            break

                        text_list.append(text)

                    span.tag(TagDbSqlParameters(f"[{','.join(text_list)}]"))

                return self._self_cur.executemany(query, vars_list, *args, **kwargs)

        def stream(self, query, vars=None, *args, **kwargs):
            dsn = self.connection.info.get_parameters()
            port = self.connection.info.port
            peer = f"{dsn['host']}:{str(port)}"

            with get_context().new_exit_span(op='PostgreSLQ/Psycopg/stream', peer=peer,
                                             component=Component.Psycopg) as span:
                span.layer = Layer.Database

                span.tag(TagDbType('PostgreSQL'))
                span.tag(TagDbInstance(dsn['dbname']))
                span.tag(TagDbStatement(query))

                if config.sql_parameters_length and vars is not None:
                    text = ','.join(str(v) for v in vars)

                    if len(text) > config.sql_parameters_length:
                        text = f'{text[:config.sql_parameters_length]}...'

                    span.tag(TagDbSqlParameters(f'[{text}]'))

                yield from self._self_cur.stream(query, vars, *args, **kwargs)

    class ProxyConnection(wrapt.ObjectProxy):
        def __init__(self, conn):
            wrapt.ObjectProxy.__init__(self, conn)

            self._self_conn = conn

        def __enter__(self):
            return ProxyConnection(wrapt.ObjectProxy.__enter__(self))

        def cursor(self, *args, **kwargs):
            return ProxyCursor(self._self_conn.cursor(*args, **kwargs))

    def connect(*args, **kwargs):
        return ProxyConnection(_connect(*args, **kwargs))

    _connect = psycopg.Connection.connect
    psycopg.Connection.connect = connect
    psycopg.connect = connect


def install_async():
    import wrapt  # psycopg is read-only C extension objects so they need to be proxied
    import psycopg

    class ProxyAsyncCursor(wrapt.ObjectProxy):
        def __init__(self, cur):
            wrapt.ObjectProxy.__init__(self, cur)

            self._self_cur = cur

        async def __aenter__(self):
            return self  # return ProxyAsyncCursor(await self._self_cur.__aenter__())  # may be necessary in future version of psycopg if __aenter__() does not return self

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            return await self._self_cur.__aexit__(exc_type, exc_val, exc_tb)

        async def execute(self, query, vars=None, *args, **kwargs):
            dsn = self.connection.info.get_parameters()
            port = self.connection.info.port
            peer = f"{dsn['host']}:{str(port)}"

            with get_context().new_exit_span(op='PostgreSLQ/Psycopg/execute', peer=peer,
                                             component=Component.Psycopg) as span:
                span.layer = Layer.Database

                span.tag(TagDbType('PostgreSQL'))
                span.tag(TagDbInstance(dsn['dbname']))
                span.tag(TagDbStatement(query))

                if config.sql_parameters_length and vars is not None:
                    text = ','.join(str(v) for v in vars)

                    if len(text) > config.sql_parameters_length:
                        text = f'{text[:config.sql_parameters_length]}...'

                    span.tag(TagDbSqlParameters(f'[{text}]'))

                return await self._self_cur.execute(query, vars, *args, **kwargs)

        async def executemany(self, query, vars_list, *args, **kwargs):
            dsn = self.connection.info.get_parameters()
            port = self.connection.info.port
            peer = f"{dsn['host']}:{str(port)}"

            with get_context().new_exit_span(op='PostgreSLQ/Psycopg/executemany', peer=peer,
                                             component=Component.Psycopg) as span:
                span.layer = Layer.Database

                span.tag(TagDbType('PostgreSQL'))
                span.tag(TagDbInstance(dsn['dbname']))
                span.tag(TagDbStatement(query))

                if config.sql_parameters_length:
                    max_len = config.sql_parameters_length
                    total_len = 0
                    text_list = []

                    for vars in vars_list:
                        text = f"[{','.join(str(v) for v in vars)}]"
                        total_len += len(text)

                        if total_len > max_len:
                            text_list.append(f'{text[:max_len - total_len]}...')

                            break

                        text_list.append(text)

                    span.tag(TagDbSqlParameters(f"[{','.join(text_list)}]"))

                return await self._self_cur.executemany(query, vars_list, *args, **kwargs)

        async def stream(self, query, vars=None, *args, **kwargs):
            dsn = self.connection.info.get_parameters()
            port = self.connection.info.port
            peer = f"{dsn['host']}:{str(port)}"

            with get_context().new_exit_span(op='PostgreSLQ/Psycopg/stream', peer=peer,
                                             component=Component.Psycopg) as span:
                span.layer = Layer.Database

                span.tag(TagDbType('PostgreSQL'))
                span.tag(TagDbInstance(dsn['dbname']))
                span.tag(TagDbStatement(query))

                if config.sql_parameters_length and vars is not None:
                    text = ','.join(str(v) for v in vars)

                    if len(text) > config.sql_parameters_length:
                        text = f'{text[:config.sql_parameters_length]}...'

                    span.tag(TagDbSqlParameters(f'[{text}]'))

                async for r in self._self_cur.stream(query, vars, *args, **kwargs):
                    yield r

    class ProxyAsyncConnection(wrapt.ObjectProxy):
        def __init__(self, conn):
            wrapt.ObjectProxy.__init__(self, conn)

            self._self_conn = conn

        async def __aenter__(self):
            return self  # return ProxyAsyncConnection(await self._self_conn.__aenter__())  # may be necessary in future version of psycopg if __aenter__() does not return self

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            return await self._self_conn.__aexit__(exc_type, exc_val, exc_tb)

        def cursor(self, *args, **kwargs):
            return ProxyAsyncCursor(self._self_conn.cursor(*args, **kwargs))

    async def aconnect(*args, **kwargs):
        return ProxyAsyncConnection(await _aconnect(*args, **kwargs))

    _aconnect = psycopg.AsyncConnection.connect
    psycopg.AsyncConnection.connect = aconnect


def install():
    install_sync()
    install_async()
