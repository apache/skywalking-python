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

if __name__ == '__main__':
    import json
    import time

    import tornado.ioloop
    import tornado.web

    class MainHandler(tornado.web.RequestHandler):
        def get(self):
            time.sleep(0.5)
            self.write(json.dumps({'song': 'Despacito', 'artist': 'Luis Fonsi'}))

    def make_app():
        return tornado.web.Application([
            (r'/users', MainHandler),
        ])

    app = make_app()
    app.listen(9091, '0.0.0.0')
    tornado.ioloop.IOLoop.current().start()
