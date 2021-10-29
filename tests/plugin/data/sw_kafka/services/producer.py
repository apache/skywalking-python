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
    from flask import Flask, jsonify
    from kafka import KafkaProducer

    app = Flask(__name__)
    producer = KafkaProducer(bootstrap_servers=['kafka-server:9092'], api_version=(1, 0, 1))

    @app.route('/users', methods=['POST', 'GET'])
    def application():
        producer.send('skywalking', b'some_message_bytes')

        return jsonify({'song': 'Despacito', 'artist': 'Luis Fonsi'})

    PORT = 9090
    app.run(host='0.0.0.0', port=PORT, debug=True)
