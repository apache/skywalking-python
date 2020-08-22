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

import os
import uuid
from typing import List

service_name = os.getenv('SW_AGENT_NAME') or 'Python Service Name'  # type: str
service_instance = os.getenv('SW_AGENT_INSTANCE') or str(uuid.uuid1()).replace('-', '')  # type: str
collector_address = os.getenv('SW_AGENT_COLLECTOR_BACKEND_SERVICES') or '127.0.0.1:11800'  # type: str
protocol = (os.getenv('SW_AGENT_PROTOCOL') or 'grpc').lower()  # type: str
authentication = os.getenv('SW_AGENT_AUTHENTICATION')  # type: str
logging_level = os.getenv('SW_AGENT_LOGGING_LEVEL') or 'INFO'  # type: str
disable_plugins = (os.getenv('SW_AGENT_DISABLE_PLUGINS') or '').split(',')  # type: List[str]
mysql_trace_sql_parameters = True if os.getenv('SW_MYSQL_TRACE_SQL_PARAMETERS') and \
                                     os.getenv('SW_MYSQL_TRACE_SQL_PARAMETERS') == 'True' else False  # type: bool
mysql_sql_parameters_max_length = int(os.getenv('SW_MYSQL_SQL_PARAMETERS_MAX_LENGTH') or '512')  # type: int
pymongo_trace_parameters = True if os.getenv('SW_PYMONGO_TRACE_PARAMETERS') and \
                                   os.getenv('SW_PYMONGO_TRACE_PARAMETERS') == 'True' else False  # type: bool
pymongo_parameters_max_length = int(os.getenv('SW_PYMONGO_PARAMETERS_MAX_LENGTH') or '512')  # type: int
ignore_suffix = os.getenv('SW_IGNORE_SUFFIX') or '.jpg,.jpeg,.js,.css,.png,.bmp,.gif,.ico,.mp3,' \
                                                 '.mp4,.html,.svg '  # type: str
flask_collect_http_params = True if os.getenv('SW_FLASK_COLLECT_HTTP_PARAMS') and \
                                    os.getenv('SW_FLASK_COLLECT_HTTP_PARAMS') == 'True' else False  # type: bool
http_params_length_threshold = int(os.getenv('SW_HTTP_PARAMS_LENGTH_THRESHOLD') or '1024')  # type: int
django_collect_http_params = True if os.getenv('SW_DJANGO_COLLECT_HTTP_PARAMS') and \
                                     os.getenv('SW_DJANGO_COLLECT_HTTP_PARAMS') == 'True' else False  # type: bool
correlation_element_max_number = int(os.getenv('SW_CORRELATION_ELEMENT_MAX_NUMBER') or '3')  # type: int
correlation_value_max_length = int(os.getenv('SW_CORRELATION_VALUE_MAX_LENGTH') or '128')  # type: int
trace_ignore = True if os.getenv('SW_TRACE_IGNORE') and \
                       os.getenv('SW_TRACE_IGNORE') == 'True' else False  # type: bool
trace_ignore_path = (os.getenv('SW_TRACE_IGNORE_PATH') or '').split(',')  # type: List[str]
elasticsearch_trace_dsl = True if os.getenv('SW_ELASTICSEARCH_TRACE_DSL') and \
                                   os.getenv('SW_ELASTICSEARCH_TRACE_DSL') == 'True' else False   # type: bool


def init(
        service: str = None,
        instance: str = None,
        collector: str = None,
        protocol_type: str = 'grpc',
        token: str = None,
):
    global service_name
    service_name = service or service_name

    global service_instance
    service_instance = instance or service_instance

    global collector_address
    collector_address = collector or collector_address

    global protocol
    protocol = protocol_type or protocol

    global authentication
    authentication = token or authentication


def serialize():
    return {
        "service_name": service_name,
        "collector_address": collector_address,
        "protocol": protocol,
        "authentication": authentication,
        "logging_level": logging_level,
        "disable_plugins": disable_plugins,
        "mysql_trace_sql_parameters": mysql_trace_sql_parameters,
        "mysql_sql_parameters_max_length": mysql_sql_parameters_max_length,
        "pymongo_trace_parameters": pymongo_trace_parameters,
        "pymongo_parameters_max_length": pymongo_parameters_max_length,
        "ignore_suffix": ignore_suffix,
        "flask_collect_http_params": flask_collect_http_params,
        "http_params_length_threshold": http_params_length_threshold,
        "django_collect_http_params": django_collect_http_params,
        "correlation_element_max_number": correlation_element_max_number,
        "correlation_value_max_length": correlation_value_max_length,
        "trace_ignore": trace_ignore,
        "trace_ignore_path": trace_ignore_path
    }


def deserialize(data):
    global service_name
    service_name = data["service_name"]
    global collector_address
    collector_address = data["collector_address"]
    global protocol
    protocol = data["protocol"]
    global authentication
    authentication = data["authentication"]
    global logging_level
    logging_level = data["logging_level"]
    global disable_plugins
    disable_plugins = data["disable_plugins"]
    global mysql_trace_sql_parameters
    mysql_trace_sql_parameters = data["mysql_trace_sql_parameters"]
    global mysql_sql_parameters_max_length
    mysql_sql_parameters_max_length = data["mysql_sql_parameters_max_length"]
    global pymongo_trace_parameters
    pymongo_trace_parameters = data["pymongo_trace_parameters"]
    global pymongo_parameters_max_length
    pymongo_parameters_max_length = data["pymongo_parameters_max_length"]
    global ignore_suffix
    ignore_suffix = data["ignore_suffix"]
    global flask_collect_http_params
    flask_collect_http_params = data["flask_collect_http_params"]
    global http_params_length_threshold
    http_params_length_threshold = data["http_params_length_threshold"]
    global django_collect_http_params
    django_collect_http_params = data["django_collect_http_params"]
    global correlation_element_max_number
    correlation_element_max_number = data["correlation_element_max_number"]
    global correlation_value_max_length
    correlation_value_max_length = data["correlation_value_max_length"]
    global trace_ignore
    trace_ignore = data["trace_ignore"]
    global trace_ignore_path
    trace_ignore_path = data["trace_ignore_path"]
