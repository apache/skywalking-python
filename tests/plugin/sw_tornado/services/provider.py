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
import json
import time

from skywalking import agent, config

if __name__ == "__main__":
    config.service_name = "provider"
    config.logging_level = "DEBUG"
    agent.start()

    from skywalking import agent, config

    if __name__ == "__main__":
        import tornado.ioloop
        import tornado.web


        class MainHandler(tornado.web.RequestHandler):
            def get(self):
                time.sleep(0.5)
                self.write(json.dumps({'song': 'Despacito', 'artist': 'Luis Fonsi'}))


        def make_app():
            config.service_name = 'consumer'
            config.logging_level = 'DEBUG'
            agent.start()

            return tornado.web.Application([
                (r"users", MainHandler),
            ])


        app = make_app()
        app.listen(9091)
        tornado.ioloop.IOLoop.current().start()
