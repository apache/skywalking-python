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
from skywalking import agent, config

if __name__ == "__main__":
    config.service_name = 'consumer'
    config.logging_level = 'DEBUG'
    agent.start()

    import requests
    import tornado.ioloop
    import tornado.web

    class MainHandler(tornado.web.RequestHandler):
        def get(self):
            res = requests.get("http://provider:9091/users")
            self.write(res.text)

    def make_app():
        return tornado.web.Application([
            (r"/users", MainHandler),
        ])

    app = make_app()
    app.listen(9090, '0.0.0.0')
    tornado.ioloop.IOLoop.current().start()
