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
import re
import uuid
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import List

# In order to prevent timeouts and possible segment loss make sure QUEUE_TIMEOUT is always at least few seconds lower
# than GRPC_TIMEOUT.
GRPC_TIMEOUT = 300  # type: int
QUEUE_TIMEOUT = 240  # type: int

RE_IGNORE_PATH = re.compile('^$')  # type: re.Pattern

options = globals().copy()  # THIS MUST PRECEDE DIRECTLY BEFORE LIST OF CONFIG OPTIONS!

service_name = os.getenv('SW_AGENT_NAME') or 'Python Service Name'  # type: str
service_instance = os.getenv('SW_AGENT_INSTANCE') or str(uuid.uuid1()).replace('-', '')  # type: str
agent_namespace = os.getenv('SW_AGENT_NAMESPACE')  # type: str
collector_address = os.getenv('SW_AGENT_COLLECTOR_BACKEND_SERVICES') or '127.0.0.1:11800'  # type: str
protocol = (os.getenv('SW_AGENT_PROTOCOL') or 'grpc').lower()  # type: str
authentication = os.getenv('SW_AGENT_AUTHENTICATION')  # type: str
logging_level = os.getenv('SW_AGENT_LOGGING_LEVEL') or 'INFO'  # type: str
disable_plugins = (os.getenv('SW_AGENT_DISABLE_PLUGINS') or '').split(',')  # type: List[str]
sql_parameters_length = int(os.getenv('SW_SQL_PARAMETERS_LENGTH') or '0')  # type: int
pymongo_trace_parameters = True if os.getenv('SW_PYMONGO_TRACE_PARAMETERS') and \
                                   os.getenv('SW_PYMONGO_TRACE_PARAMETERS') == 'True' else False  # type: bool
pymongo_parameters_max_length = int(os.getenv('SW_PYMONGO_PARAMETERS_MAX_LENGTH') or '512')  # type: int
ignore_suffix = os.getenv('SW_IGNORE_SUFFIX') or '.jpg,.jpeg,.js,.css,.png,.bmp,.gif,.ico,.mp3,' \
                                                 '.mp4,.html,.svg '  # type: str
flask_collect_http_params = True if os.getenv('SW_FLASK_COLLECT_HTTP_PARAMS') and \
                                    os.getenv('SW_FLASK_COLLECT_HTTP_PARAMS') == 'True' else False  # type: bool
sanic_collect_http_params = True if os.getenv('SW_SANIC_COLLECT_HTTP_PARAMS') and \
                                    os.getenv('SW_SANIC_COLLECT_HTTP_PARAMS') == 'True' else False  # type: bool
http_params_length_threshold = int(os.getenv('SW_HTTP_PARAMS_LENGTH_THRESHOLD') or '1024')  # type: int
django_collect_http_params = True if os.getenv('SW_DJANGO_COLLECT_HTTP_PARAMS') and \
                                     os.getenv('SW_DJANGO_COLLECT_HTTP_PARAMS') == 'True' else False  # type: bool
correlation_element_max_number = int(os.getenv('SW_CORRELATION_ELEMENT_MAX_NUMBER') or '3')  # type: int
correlation_value_max_length = int(os.getenv('SW_CORRELATION_VALUE_MAX_LENGTH') or '128')  # type: int
trace_ignore_path = os.getenv('SW_TRACE_IGNORE_PATH') or ''  # type: str
elasticsearch_trace_dsl = True if os.getenv('SW_ELASTICSEARCH_TRACE_DSL') and \
                                  os.getenv('SW_ELASTICSEARCH_TRACE_DSL') == 'True' else False  # type: bool
kafka_bootstrap_servers = os.getenv('SW_KAFKA_REPORTER_BOOTSTRAP_SERVERS') or "localhost:9092"  # type: str
kafka_topic_management = os.getenv('SW_KAFKA_REPORTER_TOPIC_MANAGEMENT') or "skywalking-managements"  # type: str
kafka_topic_segment = os.getenv('SW_KAFKA_REPORTER_TOPIC_SEGMENT') or "skywalking-segments"  # type: str
celery_parameters_length = int(os.getenv('SW_CELERY_PARAMETERS_LENGTH') or '512')
profile_active = True if os.getenv('SW_AGENT_PROFILE_ACTIVE') and \
                         os.getenv('SW_AGENT_PROFILE_ACTIVE') == 'True' else False  # type: bool
profile_task_query_interval = int(os.getenv('SW_PROFILE_TASK_QUERY_INTERVAL') or '20')

options = {opt for opt in globals() if opt not in options}  # THIS MUST FOLLOW DIRECTLY AFTER LIST OF CONFIG OPTIONS!


def init(**kwargs):
    glob = globals()

    for key, val in kwargs.items():
        if key not in options:
            raise KeyError('invalid config option %s' % key)

        glob[key] = val


def finalize():
    reesc = re.compile(r'([.*+?^=!:${}()|\[\]\\])')
    suffix = r'^.+(?:' + '|'.join(reesc.sub(r'\\\1', s.strip()) for s in ignore_suffix.split(',')) + ')$'
    path = '^(?:' + \
           '|'.join(                          # replaces ","
               '(?:(?:[^/]+/)*[^/]+)?'.join(  # replaces "**"
                   '[^/]*'.join(              # replaces "*"
                       '[^/]'.join(           # replaces "?"
                           reesc.sub(r'\\\1', s) for s in p2.split('?')
                       ) for p2 in p1.split('*')
                   ) for p1 in p0.strip().split('**')
               ) for p0 in trace_ignore_path.split(',')
           ) + ')$'

    global RE_IGNORE_PATH
    RE_IGNORE_PATH = re.compile('%s|%s' % (suffix, path))


def serialize():
    glob = globals()

    return {key: glob[key] for key in options}


def deserialize(data):
    init(**data)
    finalize()
