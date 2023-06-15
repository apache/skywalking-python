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

import json

from skywalking import Layer, Component, config
from skywalking.trace.context import get_context
from skywalking.trace.tags import TagDbType, TagDbInstance, TagDbStatement, TagDbSqlParameters

link_vector = ['https://neo4j.com/docs/python-manual/5/']
support_matrix = {
    'neo4j': {
        '>=3.7': ['5.*'],
    }
}
note = """The Neo4j plugin integrates neo4j python driver 5.x.x versions which
support both Neo4j 5 and 4.4 DBMS."""


def install():
    from neo4j import AsyncSession, Session
    from neo4j._sync.work.transaction import TransactionBase
    from neo4j._async.work.transaction import AsyncTransactionBase

    _session_run = Session.run
    _async_session_run = AsyncSession.run
    _transaction_run = TransactionBase.run
    _async_transaction_run = AsyncTransactionBase.run

    def _archive_span(span, database, query, parameters, **kwargs):
        span.layer = Layer.Database
        span.tag(TagDbType('Neo4j'))
        span.tag(TagDbInstance(database or ''))
        span.tag(TagDbStatement(query))

        parameters = dict(parameters or {}, **kwargs)
        if config.plugin_sql_parameters_max_length and parameters:
            parameter = json.dumps(parameters, ensure_ascii=False)
            max_len = config.plugin_sql_parameters_max_length
            parameter = f'{parameter[0:max_len]}...' if len(
                parameter) > max_len else parameter
            span.tag(TagDbSqlParameters(f'[{parameter}]'))

    def get_peer(address):
        return f'{address.host}:{address.port}'

    def _sw_session_run(self, query, parameters, **kwargs):
        with get_context().new_exit_span(
                op='Neo4j/Session/run',
                peer=get_peer(self._pool.address),
                component=Component.Neo4j) as span:
            _archive_span(span, self._config.database, query, parameters, **kwargs)
            return _session_run(self, query, parameters, **kwargs)

    def _sw_transaction_run(self, query, parameters=None, **kwargs):
        with get_context().new_exit_span(
                op='Neo4j/Transaction/run',
                peer=get_peer(self._connection.unresolved_address),
                component=Component.Neo4j) as span:
            _archive_span(span, self._database, query, parameters, **kwargs)
            return _transaction_run(self, query, parameters, **kwargs)

    async def _sw_async_session_run(self, query, parameters, **kwargs):
        with get_context().new_exit_span(
                op='Neo4j/AsyncSession/run',
                peer=get_peer(self._pool.address),
                component=Component.Neo4j) as span:
            _archive_span(span, self._config.database, query, parameters, **kwargs)
            return await _async_session_run(self, query, parameters, **kwargs)

    async def _sw_async_transaction_run(self, query, parameters, **kwargs):
        with get_context().new_exit_span(
                op='Neo4j/AsyncTransaction/run',
                peer=get_peer(self._connection.unresolved_address),
                component=Component.Neo4j) as span:
            _archive_span(span, self._database, query, parameters, **kwargs)
            return await _async_transaction_run(self, query, parameters, **kwargs)

    Session.run = _sw_session_run
    AsyncSession.run = _sw_async_session_run
    TransactionBase.run = _sw_transaction_run
    AsyncTransactionBase.run = _sw_async_transaction_run
