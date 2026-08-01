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
import time

if __name__ == '__main__':
    from flask import Flask, jsonify

    # explicit os.fork() with SW_AGENT_EXPERIMENTAL_FORK_SUPPORT=true:
    # the child must restart the agent as a `-child(pid)` instance and keep tracing.
    # Fork outside the agent's active-RPC window (right after start the agent registers
    # with the collector; forking mid-RPC trips gRPC's own at-fork races, grpc/grpc#43055)
    time.sleep(2)
    pid = os.fork()

    if pid == 0:
        backend = Flask('backend')

        @backend.route('/users', methods=['GET'])
        def users():
            return jsonify({'song': 'Despacito'})

        backend.run(host='0.0.0.0', port=9091)
    else:
        import socket
        import requests

        # serve only once the forked child's backend is reachable, so early readiness
        # probes cannot produce error spans through an instrumented parent
        for _ in range(120):
            try:
                socket.create_connection(('127.0.0.1', 9091), timeout=1).close()
                break
            except OSError:
                time.sleep(1)

        frontend = Flask('frontend')

        # readiness/warm-up endpoint: its segment arrives alone and seeds the service name
        # in the mock collector, whose first-insert for a service is not concurrency-safe
        # (SegmentItems.addSegmentItem check-then-act) — the parent and child later report
        # their /users segments concurrently under the same service name
        @frontend.route('/ping', methods=['GET'])
        def ping():
            return jsonify({'song': 'Despacito'})

        @frontend.route('/users', methods=['GET'])
        def call_backend():
            res = requests.get('http://127.0.0.1:9091/users', timeout=5)
            return jsonify(res.json())

        frontend.run(host='0.0.0.0', port=9090)
