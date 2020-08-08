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

import requests

from skywalking import agent, config
from skywalking.decorators import runnable

if __name__ == '__main__':
    config.service_name = 'consumer'
    config.logging_level = 'DEBUG'
    config.flask_collect_http_params = True
    agent.start()

    from flask import Flask, jsonify

    app = Flask(__name__)

    @app.route("/users", methods=["POST", "GET"])
    def application():
        from skywalking.trace.context import get_context
        get_context().put_correlation("correlation", "correlation")

        @runnable(op="/test")
        def post():
            requests.post("http://provider:9091/users")

        from threading import Thread
        t = Thread(target=post)
        t.start()

        res = requests.post("http://provider:9091/users")

        t.join()

        return jsonify(res.json())

    PORT = 9090
    app.run(host='0.0.0.0', port=PORT, debug=True)
