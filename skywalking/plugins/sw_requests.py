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
import traceback

from skywalking import Layer, Component
from skywalking.trace import tags
from skywalking.trace.carrier import Carrier
from skywalking.trace.context import get_context
from skywalking.trace.tags import Tag
from skywalking import config

logger = logging.getLogger(__name__)


def install():
    # noinspection PyBroadException
    try:
        from requests import Session

        _request = Session.request

        def _sw_request(this: Session, method, url,
                        params=None, data=None, headers=None, cookies=None, files=None,
                        auth=None, timeout=None, allow_redirects=True, proxies=None,
                        hooks=None, stream=None, verify=None, cert=None, json=None):

            from urllib.parse import urlparse
            url_param = urlparse(url)

            # ignore trace skywalking self request
            if config.protocol == 'http' and config.collector_address.rstrip('/').endswith(url_param.netloc):
                return _request(this, method, url, params, data, headers, cookies, files, auth, timeout,
                                allow_redirects,
                                proxies,
                                hooks, stream, verify, cert, json)

            context = get_context()
            carrier = Carrier()
            with context.new_exit_span(op=url_param.path or "/", peer=url_param.netloc, carrier=carrier) as span:
                span.layer = Layer.Http
                span.component = Component.Requests

                if headers is None:
                    headers = {}
                    for item in carrier:
                        headers[item.key] = item.val
                else:
                    for item in carrier:
                        headers[item.key] = item.val

                try:
                    res = _request(this, method, url, params, data, headers, cookies, files, auth, timeout,
                                   allow_redirects,
                                   proxies,
                                   hooks, stream, verify, cert, json)

                    span.tag(Tag(key=tags.HttpMethod, val=method.upper()))
                    span.tag(Tag(key=tags.HttpUrl, val=url))
                    span.tag(Tag(key=tags.HttpStatus, val=res.status_code))
                    if res.status_code >= 400:
                        span.error_occurred = True
                except BaseException as e:
                    span.raised()
                    raise e
                return res

        Session.request = _sw_request
    except Exception:
        logger.warning('failed to install plugin %s', __name__)
        traceback.print_exc()
