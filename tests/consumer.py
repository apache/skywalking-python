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
from urllib import request

from skywalking import agent, config

if __name__ == '__main__':
    config.service_name = 'consumer'
    config.logging_level = 'DEBUG'
    agent.start()

    import socketserver
    from http.server import BaseHTTPRequestHandler

    provider_url = os.getenv('PROVIDER_URL') or 'http://localhost:9091/'

    class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):

        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            req = request.Request(provider_url + '/whatever')
            with request.urlopen(req) as res:
                self.wfile.write(res.read(300))

        def do_POST(self):
            self.do_GET()

    PORT = 9090
    Handler = SimpleHTTPRequestHandler

    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print("serving at port", PORT)
        httpd.serve_forever()
