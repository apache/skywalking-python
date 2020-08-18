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
from skywalking.trace.context import get_context
from skywalking.trace.tags import Tag

logger = logging.getLogger(__name__)


def install():
    # noinspection PyBroadException
    try:
        from kubernetes.client.rest import RESTClientObject

        _request = RESTClientObject.request

        def _sw_request(this: RESTClientObject, method, url, query_params=None, headers=None,
                        body=None, post_params=None, _preload_content=True,
                        _request_timeout=None):

            from urllib.parse import urlparse
            url_param = urlparse(url)

            context = get_context()
            with context.new_exit_span(op=url_param.path or "/", peer=url_param.netloc) as span:
                span.layer = Layer.Http
                span.component = Component.Kubernetes
                try:
                    res = _request(this, method, url, query_params=query_params, headers=headers,
                                   post_params=post_params, body=body, _preload_content=_preload_content,
                                   _request_timeout=_request_timeout)

                    span.tag(Tag(key=tags.HttpMethod, val=method.upper()))
                    span.tag(Tag(key=tags.HttpUrl, val=url))
                    span.tag(Tag(key=tags.HttpStatus, val=res.status))
                    if res.status >= 400:
                        span.error_occurred = True
                except BaseException as e:
                    span.raised()
                    raise e
                return res

        RESTClientObject.request = _sw_request
    except Exception:
        logger.warning('failed to install plugin %s', __name__)
