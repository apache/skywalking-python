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
    'psycopg2-binary': {
        '>=3.10': [],
        '>=3.6': ['2.9']  # transition to psycopg(3), not working for python 3.10
    }
}
note = """"""


def install():
    import wrapt  # psycopg2 is read-only C extension objects so they need to be proxied
    import psycopg2

    class ProxyCursor(wrapt.ObjectProxy):
        def __init__(self, cur):
            wrapt.ObjectProxy.__init__(self, cur)

            self._self_cur = cur

        def __enter__(self):
            return ProxyCursor(wrapt.ObjectProxy.__enter__(self))

        def execute(self, query, vars=None):
            dsn = self.connection.get_dsn_parameters()
            peer = f"{dsn['host']}:{dsn['port']}"

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

                return self._self_cur.execute(query, vars)

        def executemany(self, query, vars_list):
            dsn = self.connection.get_dsn_parameters()
            peer = f"{dsn['host']}:{dsn['port']}"

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

                return self._self_cur.executemany(query, vars_list)

        def callproc(self, procname, parameters=None):
            dsn = self.connection.get_dsn_parameters()
            peer = f"{dsn['host']}:{dsn['port']}"

            with get_context().new_exit_span(op='PostgreSLQ/Psycopg/callproc', peer=peer,
                                             component=Component.Psycopg) as span:
                span.layer = Layer.Database
                args = f"({'' if not parameters else ','.join(parameters)})"

                span.tag(TagDbType('PostgreSQL'))
                span.tag(TagDbInstance(dsn['dbname']))
                span.tag(TagDbStatement(procname + args))

                return self._self_cur.callproc(procname, parameters)

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

    _connect = psycopg2.connect
    psycopg2.connect = connect
