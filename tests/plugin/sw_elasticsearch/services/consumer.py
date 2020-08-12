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

from elasticsearch import Elasticsearch
from skywalking import agent, config

if __name__ == '__main__':
    config.service_name = 'consumer'
    config.logging_level = 'DEBUG'
    config.elasticsearch_trace_dsl = True
    agent.start()

    from flask import Flask, jsonify

    app = Flask(__name__)
    client = Elasticsearch('http://elasticsearch:9200/')
    index_name = "test"

    def create_index():
        client.indices.create(index=index_name, ignore=400)

    def save_index():
        data = {"song": "Despacito", "artist": "Luis Fonsi"}
        client.index(index=index_name, doc_type="test", id=1, body=data)

    def search():
        client.get(index=index_name, id=1)

    @app.route("/users", methods=["POST", "GET"])
    def application():
        create_index()
        save_index()
        search()
        return jsonify({"song": "Despacito", "artist": "Luis Fonsi"})

    PORT = 9090
    app.run(host='0.0.0.0', port=PORT, debug=True)
