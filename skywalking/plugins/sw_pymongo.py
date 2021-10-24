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
from skywalking.trace.tags import TagDbType, TagDbInstance, TagDbStatement

link_vector = ['https://pymongo.readthedocs.io']
support_matrix = {
    'pymongo': {
        '>=3.6': ['3.11']  # TODO: "3.12" incompatible with all python versions, need investigation
    }
}
note = """"""


def install():
    from pymongo.bulk import _Bulk
    from pymongo.cursor import Cursor
    from pymongo.pool import SocketInfo

    bulk_op_map = {
        0: 'insert',
        1: 'update',
        2: 'delete'
    }
    # handle insert_many and bulk write
    inject_bulk_write(_Bulk, bulk_op_map)

    # handle find() & find_one()
    inject_cursor(Cursor)

    # handle other commands
    inject_socket_info(SocketInfo)


def inject_socket_info(SocketInfo): # noqa
    _command = SocketInfo.command

    def _sw_command(this: SocketInfo, dbname, spec, *args, **kwargs):
        # pymongo sends `ismaster` command continuously. ignore it.
        if spec.get('ismaster') is None:
            address = this.sock.getpeername()
            peer = f'{address[0]}:{address[1]}'
            context = get_context()

            operation = list(spec.keys())[0]
            sw_op = f'{operation.capitalize()}Operation'
            with context.new_exit_span(op=f'MongoDB/{sw_op}', peer=peer, component=Component.MongoDB) as span:
                result = _command(this, dbname, spec, *args, **kwargs)

                span.layer = Layer.Database
                span.tag(TagDbType('MongoDB'))
                span.tag(TagDbInstance(dbname))

                if config.pymongo_trace_parameters:
                    # get filters
                    filters = _get_filter(operation, spec)
                    max_len = config.pymongo_parameters_max_length
                    filters = f'{filters[0:max_len]}...' if len(filters) > max_len else filters
                    span.tag(TagDbStatement(filters))

        else:
            result = _command(this, dbname, spec, *args, **kwargs)

        return result

    SocketInfo.command = _sw_command


def _get_filter(request_type, spec):
    """
    :param request_type: the request param send to MongoDB
    :param spec: maybe a bson.SON class or a dict
    :return: filter string
    """
    from bson import SON

    if isinstance(spec, SON):
        spec = spec.to_dict()
        spec.pop(request_type)
    elif isinstance(spec, dict):
        spec = dict(spec)
        spec.pop(request_type)

    return f'{request_type} {str(spec)}'


def inject_bulk_write(_Bulk, bulk_op_map): # noqa
    _execute = _Bulk.execute

    def _sw_execute(this: _Bulk, *args, **kwargs):
        nodes = this.collection.database.client.nodes
        peer = ','.join([f'{address[0]}:{address[1]}' for address in nodes])
        context = get_context()

        sw_op = 'MixedBulkWriteOperation'
        with context.new_exit_span(op=f'MongoDB/{sw_op}', peer=peer, component=Component.MongoDB) as span:
            span.layer = Layer.Database

            bulk_result = _execute(this, *args, **kwargs)

            span.tag(TagDbType('MongoDB'))
            span.tag(TagDbInstance(this.collection.database.name))
            if config.pymongo_trace_parameters:
                filters = ''
                bulk_ops = this.ops
                for bulk_op in bulk_ops:
                    opname = bulk_op_map.get(bulk_op[0])
                    _filter = f'{opname} {str(bulk_op[1])}'
                    filters = f'{filters + _filter} '

                max_len = config.pymongo_parameters_max_length
                filters = f'{filters[0:max_len]}...' if len(filters) > max_len else filters
                span.tag(TagDbStatement(filters))

            return bulk_result

    _Bulk.execute = _sw_execute


def inject_cursor(Cursor): # noqa
    __send_message = Cursor._Cursor__send_message

    def _sw_send_message(this: Cursor, operation):
        nodes = this.collection.database.client.nodes
        peer = ','.join([f'{address[0]}:{address[1]}' for address in nodes])

        context = get_context()
        op = 'FindOperation'

        with context.new_exit_span(op=f'MongoDB/{op}', peer=peer, component=Component.MongoDB) as span:
            span.layer = Layer.Database

            # __send_message return nothing
            __send_message(this, operation)

            span.tag(TagDbType('MongoDB'))
            span.tag(TagDbInstance(this.collection.database.name))

            if config.pymongo_trace_parameters:
                filters = f'find {str(operation.spec)}'
                max_len = config.pymongo_parameters_max_length
                filters = f'{filters[0:max_len]}...' if len(filters) > max_len else filters
                span.tag(TagDbStatement(filters))

            return

    Cursor._Cursor__send_message = _sw_send_message
