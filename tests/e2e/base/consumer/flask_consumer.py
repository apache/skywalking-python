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

"""
This module contains the Consumer part of the e2e tests.
consumer (Flask) -> consumer (requests) -> provider (FastAPI + logging_with_exception)
"""
from gevent import monkey
monkey.patch_all()
import grpc.experimental.gevent as grpc_gevent     # key point
grpc_gevent.init_gevent()   # key point
from skywalking import config, agent  
config.logging_level = 'DEBUG'
config.init()
agent.start()

from flask import Flask, request
import requests


app = Flask(__name__)
   
@app.route('/artist', methods=['GET', 'POST'])
def artist():
    try:
        payload = request.get_json()
        with requests.Session() as session:
            with session.post('http://provider:9090/artist', data=payload) as response:
                return response.json()
    except Exception as e:  # noqa
        print(f"error: {e}")
        return {'message': e}



# if __name__ == '__main__':
#     # noinspection PyTypeChecker
#     app.run(host='0.0.0.0', port=9090)
