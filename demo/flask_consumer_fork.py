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

import os

from flask import Flask
from skywalking import agent, config
import requests

# Profiling only available in gRPC, meter only in kafka + grpc
config.init(agent_collector_backend_services='localhost:11800', agent_protocol='grpc',
            agent_name='great-app-consumer-grpc',
            kafka_bootstrap_servers='localhost:9094',  # If you use kafka, set this
            agent_instance_name='instance-01',
            agent_experimental_fork_support=True, agent_logging_level='DEBUG', agent_log_reporter_active=True,
            agent_meter_reporter_active=True,
            agent_profile_active=True)

agent.start()

parent_pid = os.getpid()
pid = os.fork()

app = Flask(__name__)


@app.route('/', methods=['POST', 'GET'])
def application():
    res = requests.get('http://localhost:9999')
    return res.json()


if __name__ == '__main__':
    PORT = 9097 if pid == 0 else 9098  # 0 is child process
    app.run(host='0.0.0.0', port=PORT, debug=False)  # RELOADER IS ALSO FORKED
