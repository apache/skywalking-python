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

link_vector = ['https://mysqlclient.readthedocs.io/']
support_matrix = {
    'mysqlclient': {
        '>=3.6': ['2.1.0']
    }
}
note = """"""


def install():
    import wrapt
    import MySQLdb

    _connect = MySQLdb.connect

    def _sw_connect(*args, **kwargs):
        con = _connect(*args, **kwargs)
        con.host = kwargs['host']
        con.db = kwargs['db']
        return ProxyConnection(con)

    class ProxyCursor(wrapt.ObjectProxy):
        def __init__(self, cur):
            wrapt.ObjectProxy.__init__(self, cur)

            self._self_cur = cur

        def __enter__(self):
            return ProxyCursor(wrapt.ObjectProxy.__enter__(self))

        def execute(self, query, args=None):
            peer = f'{self.connection.host}:{self.connection.port}'
            with get_context().new_exit_span(op='Mysql/MysqlClient/execute', peer=peer,
                                             component=Component.MysqlClient) as span:
                span.layer = Layer.Database
                span.tag(TagDbType('mysql'))
                span.tag(TagDbInstance((self.connection.db or '')))
                span.tag(TagDbStatement(query))

                if config.sql_parameters_length and args:
                    parameter = ','.join([str(arg) for arg in args])
                    max_len = config.sql_parameters_length
                    parameter = f'{parameter[0:max_len]}...' if len(parameter) > max_len else parameter
                    span.tag(TagDbSqlParameters(f'[{parameter}]'))

                return self._self_cur.execute(query, args)

    class ProxyConnection(wrapt.ObjectProxy):
        def __init__(self, conn):
            wrapt.ObjectProxy.__init__(self, conn)

            self._self_conn = conn

        def __enter__(self):
            return ProxyConnection(wrapt.ObjectProxy.__enter__(self))

        def cursor(self, cursorclass=None):
            return ProxyCursor(self._self_conn.cursor(cursorclass))

    MySQLdb.connect = _sw_connect
