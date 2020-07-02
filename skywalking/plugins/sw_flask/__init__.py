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
from skywalking.trace.span import NoopSpan
from skywalking.trace.tags import Tag

logger = logging.getLogger(__name__)


def install():
    # noinspection PyBroadException
    try:
        from flask import Flask
        _full_dispatch_request = Flask.full_dispatch_request

        _handle_user_exception = Flask.handle_user_exception

        def _sw_full_dispatch_request(this: Flask):
            import flask
            req = flask.request
            context = get_context()
            carrier = Carrier()

            for item in carrier:
                if item.key.capitalize() in req.headers:
                    item.val = req.headers[item.key.capitalize()]
            with context.new_entry_span(op=req.path, carrier=carrier) as span:
                span.layer = Layer.Http
                span.component = Component.Flask
                span.peer = '%s:%s' % (req.environ["REMOTE_ADDR"], req.environ["REMOTE_PORT"])
                span.tag(Tag(key=tags.HttpMethod, val=req.method))
                span.tag(Tag(key=tags.HttpUrl, val=req.url))
                resp = _full_dispatch_request(this)

                if resp.status_code >= 400:
                    span.error_occurred = True

                span.tag(Tag(key=tags.HttpStatus, val=resp.status_code))
                return resp

        def _sw_handle_user_exception(this: Flask, e):
            if e is not None:
                entry_span = get_context().active_span()
                if entry_span is not None and type(entry_span) is not NoopSpan:
                    entry_span.raised()

            return _handle_user_exception(this, e)

        Flask.full_dispatch_request = _sw_full_dispatch_request
        Flask.handle_user_exception = _sw_handle_user_exception

    except Exception:
        logger.warning('failed to install plugin %s', __name__)
