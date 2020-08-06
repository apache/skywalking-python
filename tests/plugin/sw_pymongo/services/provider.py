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

import time

from skywalking import agent, config
from flask import Flask, jsonify
from pymongo import MongoClient


config.service_name = "provider"
config.logging_level = "DEBUG"
config.pymongo_trace_parameters = True
agent.start()


client = MongoClient('mongodb://mongo:27017/')
db = client['test-database']
collection = db['test-collection']


app = Flask(__name__)


@app.route("/insert_many", methods=["GET"])
def test_insert_many():
    time.sleep(0.5)
    new_posts = [{"song": "Despacito"},
                 {"artist": "Luis Fonsi"}]
    result = collection.insert_many(new_posts)
    return jsonify({"ok": result.acknowledged})


@app.route("/find_one", methods=["GET"])
def test_find_one():
    time.sleep(0.5)
    result = collection.find_one({"song": "Despacito"})
    # have to get the result and use it. if not lint will report error
    print(result)
    return jsonify({"song": "Despacito"})


@app.route("/delete_one", methods=["GET"])
def test_delete_one():
    time.sleep(0.5)
    result = collection.delete_one({"song": "Despacito"})
    return jsonify({"ok": result.acknowledged})


if __name__ == '__main__':
    PORT = 9091
    app.run(host="0.0.0.0", port=PORT, debug=True)
