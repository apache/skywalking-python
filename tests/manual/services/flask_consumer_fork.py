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

config.init(collector_address='localhost:11800', protocol='grpc', service_name='great-app-consumer-grpc',
            kafka_bootstrap_servers='localhost:9094',  # If you use kafka, set this
            service_instance='instance-01',
            experimental_fork_support=True, logging_level='DEBUG', log_reporter_active=True,
            meter_reporter_active=True,
            profiler_active=True)

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
