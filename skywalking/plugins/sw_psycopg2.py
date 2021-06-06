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
from skywalking.trace import tags
from skywalking.trace.context import get_context
from skywalking.trace.tags import Tag


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
            peer = dsn['host'] + ':' + dsn['port']

            with get_context().new_exit_span(op="PostgreSLQ/Psycopg/execute", peer=peer) as span:
                span.layer = Layer.Database
                span.component = Component.Psycopg

                span.tag(Tag(key=tags.DbType, val="PostgreSQL"))
                span.tag(Tag(key=tags.DbInstance, val=dsn['dbname']))
                span.tag(Tag(key=tags.DbStatement, val=query))

                if config.mysql_trace_sql_parameters and vars is not None:
                    max_len = config.mysql_sql_parameters_max_length
                    text = ','.join(str(v) for v in vars)

                    if len(text) > max_len:
                        text = text[:max_len] + '...'

                    span.tag(Tag(key=tags.DbSqlParameters, val='[' + text + ']'))

                return self._self_cur.execute(query, vars)

        def executemany(self, query, vars_list):
            dsn = self.connection.get_dsn_parameters()
            peer = dsn['host'] + ':' + dsn['port']

            with get_context().new_exit_span(op="PostgreSLQ/Psycopg/executemany", peer=peer) as span:
                span.layer = Layer.Database
                span.component = Component.Psycopg

                span.tag(Tag(key=tags.DbType, val="PostgreSQL"))
                span.tag(Tag(key=tags.DbInstance, val=dsn['dbname']))
                span.tag(Tag(key=tags.DbStatement, val=query))

                if config.mysql_trace_sql_parameters:
                    max_len = config.mysql_sql_parameters_max_length
                    total_len = 0
                    text_list = []

                    for vars in vars_list:
                        text = '[' + ','.join(str(v) for v in vars) + ']'
                        total_len += len(text)

                        if total_len > max_len:
                            text_list.append(text[:max_len - total_len] + '...')

                            break

                        text_list.append(text)

                    span.tag(Tag(key=tags.DbSqlParameters, val='[' + ','.join(text_list) + ']'))

                return self._self_cur.executemany(query, vars_list)

        def callproc(self, procname, parameters=None):
            dsn = self.connection.get_dsn_parameters()
            peer = dsn['host'] + ':' + dsn['port']

            with get_context().new_exit_span(op="PostgreSLQ/Psycopg/callproc", peer=peer) as span:
                span.layer = Layer.Database
                span.component = Component.Psycopg
                args = '(' + ('' if not parameters else ','.join(parameters)) + ')'

                span.tag(Tag(key=tags.DbType, val="PostgreSQL"))
                span.tag(Tag(key=tags.DbInstance, val=dsn['dbname']))
                span.tag(Tag(key=tags.DbStatement, val=procname + args))

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
