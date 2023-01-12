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
from skywalking.trace.tags import TagDbType, TagDbStatement

link_vector = ['https://happybase.readthedocs.io']
support_matrix = {
    'happybase': {
        '>=3.7': ['1.2.0'],
    }
}
note = """"""


def install():
    from happybase import Table
    from happybase import Connection
    _row = Table.row
    _rows = Table.rows
    _cells = Table.cells
    _scan = Table.scan
    _put = Table.put
    _delete = Table.delete
    _create_table = Connection.create_table

    def bytes2str(value):
        if isinstance(value, bytes):
            return value.decode()
        return value

    def _sw_create_table(this, name, families):
        context = get_context()
        peer = ','.join([f'{this.host}:{str(this.port)}'])
        table_name = name
        with context.new_exit_span(op=f'HBase/create/{table_name}', peer=peer,
                                   component=Component.HBase) as span:
            span.layer = Layer.Database
            span.tag(TagDbType('HBase'))
            span.tag(TagDbStatement(''))
            _create_table(this, name, families)

    def _sw_hbase_opt(table, name, fun, row, is_return=True):
        context = get_context()
        peer = ','.join([f'{table.connection.host}:{str(table.connection.port)}'])
        table_name = bytes2str(table.name)
        row = bytes2str(row)
        with context.new_exit_span(op=f'HBase/{name}/{table_name}/{row}', peer=peer,
                                   component=Component.HBase) as span:
            span.layer = Layer.Database
            span.tag(TagDbType('HBase'))
            span.tag(TagDbStatement(''))
            if is_return:
                return fun()
            else:
                fun()

    def _sw_row(this, row, columns=None, timestamp=None, include_timestamp=False):
        def __sw_row():
            return _row(this, row, columns, timestamp, include_timestamp)

        res = _sw_hbase_opt(this, 'row', __sw_row, row)
        return res

    def _sw_rows(this, rows, columns=None, timestamp=None, include_timestamp=False):
        def __sw_rows():
            return _rows(this, rows, columns, timestamp, include_timestamp)

        row = ''
        if rows and isinstance(rows, list):
            row = rows[0]

        res = _sw_hbase_opt(this, 'rows', __sw_rows, row)
        return res

    def _sw_cells(this, row, column, versions=None, timestamp=None, include_timestamp=False):
        def __sw_cells():
            return _cells(this, row, column, versions, timestamp, include_timestamp)

        res = _sw_hbase_opt(this, 'cells', __sw_cells, row)
        return res

    def _sw_scan(this, row_start=None, row_stop=None, row_prefix=None,
                 columns=None, filter=None, timestamp=None,
                 include_timestamp=False, batch_size=1000, scan_batching=None,
                 limit=None, sorted_columns=False, reverse=False):
        def __sw_scan():
            return _scan(this, row_start, row_stop, row_prefix,
                         columns, filter, timestamp,
                         include_timestamp, batch_size, scan_batching,
                         limit, sorted_columns, reverse)

        res = _sw_hbase_opt(this, 'scan', __sw_scan, row_start)
        return res

    def _sw_put(this, row, data, timestamp=None, wal=True):
        def __sw_put():
            return _put(this, row, data, timestamp, wal)

        _sw_hbase_opt(this, 'put', __sw_put, row, False)

    def _sw_delete(this, row, columns=None, timestamp=None, wal=True):
        def __sw_delete():
            return _delete(this, row, columns, timestamp, wal)

        _sw_hbase_opt(this, 'delete', __sw_delete, row, False)

    Table.row = _sw_row
    Table.rows = _sw_rows
    Table.cells = _sw_cells
    Table.scan = _sw_scan
    Table.put = _sw_put
    Table.delete = _sw_delete
    Connection.create_table = _sw_create_table
