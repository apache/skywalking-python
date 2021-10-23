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

link_vector = ['https://pymysql.readthedocs.io/en/latest/']
support_matrix = {
    'pymysql': {
        '>=3.6': ['1.0']
    }
}
note = """"""


def install():
    from pymysql.cursors import Cursor

    _execute = Cursor.execute

    def _sw_execute(this: Cursor, query, args=None):
        peer = f'{this.connection.host}:{this.connection.port}'

        context = get_context()
        with context.new_exit_span(op='Mysql/PyMsql/execute', peer=peer, component=Component.PyMysql) as span:
            span.layer = Layer.Database
            res = _execute(this, query, args)

            span.tag(TagDbType('mysql'))
            span.tag(TagDbInstance((this.connection.db or b'').decode('utf-8')))
            span.tag(TagDbStatement(query))

            if config.sql_parameters_length and args:
                parameter = ','.join([str(arg) for arg in args])
                max_len = config.sql_parameters_length
                parameter = f'{parameter[0:max_len]}...' if len(parameter) > max_len else parameter
                span.tag(TagDbSqlParameters(f'[{parameter}]'))

            return res

    Cursor.execute = _sw_execute
