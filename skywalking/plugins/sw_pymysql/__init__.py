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
import logging

from skywalking import Layer, Component
from skywalking.trace import tags
from skywalking.trace.carrier import Carrier
from skywalking.trace.context import get_context
from skywalking.trace.tags import Tag

logger = logging.getLogger(__name__)


def install():
    # noinspection PyBroadException
    try:
        from pymysql.cursors import Cursor

        _execute = Cursor.execute

        def _sw_execute(this: Cursor, query, args=None):
            peer = "%s:%s" % (this.connection.host, this.connection.port)

            context = get_context()
            carrier = Carrier()
            with context.new_exit_span(op="Mysql/PyMsql/execute", peer=peer, carrier=carrier) as span:
                span.layer = Layer.Database
                span.component = Component.PyMysql
                try:
                    res = _execute(this, query, args)

                    span.tag(Tag(key=tags.DbType, val="mysql"))
                    span.tag(Tag(key=tags.DbInstance, val=this.connection.db.decode("utf-8")))
                    span.tag(Tag(key=tags.DbStatement, val=query))

                except BaseException as e:
                    span.raised()
                    raise e
                return res

        Cursor.execute = _sw_execute
    except Exception:
        logger.warning('failed to install plugin %s', __name__)
