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
from flask import Flask, jsonify

try:
    # under gunicorn --preload this module imports in the PRE-FORK master, where the
    # agent is instrumentation-only: this instrumented call must silently noop
    # (NoopSpan via agent.started() guard) instead of crashing the master
    requests.get('http://collector:12800/receiveData', timeout=5)
except Exception:  # noqa
    pass

app = Flask(__name__)


@app.route('/users', methods=['GET'])
def users():
    return jsonify({'song': 'Despacito'})
