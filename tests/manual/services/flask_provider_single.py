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
from flask import Flask, jsonify
from skywalking import agent, config

config.init(collector_address='localhost:12800', protocol='http', service_name='great-app-provider-http',
            service_instance='instance-01',
            experimental_fork_support=True, logging_level='DEBUG', log_reporter_active=True,
            meter_reporter_active=True,
            profiler_active=True)

agent.start()

app = Flask(__name__)


@app.route('/', methods=['POST', 'GET'])
def application():
    return jsonify({'status': 'ok'})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=9999, debug=True)
