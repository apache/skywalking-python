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
from urllib import request
from wsgiref.simple_server import make_server

from pyramid.config import Configurator
from pyramid.response import Response

from skywalking import agent, config


def index(req):
    data = '{"name": "whatever"}'.encode('utf8')
    req = request.Request(f'http://provider:9091/{req.path.lstrip("/")}')
    req.add_header('Content-Type', 'application/json; charset=utf-8')
    req.add_header('Content-Length', str(len(data)))
    with request.urlopen(req, data):
        return Response(data)


if __name__ == '__main__':
    config.service_name = 'consumer'
    agent.start()

    with Configurator() as config:
        config.add_route('pyramid', '/pyramid')
        config.add_view(index, route_name='pyramid')

        app = config.make_wsgi_app()

    server = make_server('0.0.0.0', 9090, app)

    server.serve_forever()
