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
    import pulsar
    from flask import Flask, jsonify
    from pulsar import BatchingType

    app = Flask(__name__)
    client = pulsar.Client(service_url='pulsar://pulsar-server:6650')
    producer = client.create_producer(
        'sw-topic',
        block_if_queue_full=True,
        batching_enabled=True,
        batching_max_publish_delay_ms=10,
        batching_type=BatchingType.KeyBased
    )


    @app.route('/users', methods=['POST', 'GET'])
    def application():
        producer.send('I love skywalking 3 thousand'.encode('utf-8'), None)
        producer.flush()
        producer.close()
        return jsonify({'song': 'Despacito', 'artist': 'Luis Fonsi'})

    PORT = 9090
    app.run(host='0.0.0.0', port=PORT, debug=True)
