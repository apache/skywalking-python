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


from skywalking import agent, config

if __name__ == '__main__':
    config.service_name = 'producer'
    config.logging_level = 'INFO'
    agent.start()

    from flask import Flask, jsonify
    app = Flask(__name__)
    import pika
    parameters = (pika.URLParameters("amqp://admin:admin@rabbitmq-server:5672/%2F"))

    @app.route("/users", methods=["POST", "GET"])
    def application():
        connection = pika.BlockingConnection(parameters)
        channel = connection.channel()
        channel.queue_declare("test")
        channel.exchange_declare("test")
        channel.queue_bind(exchange='test', queue="test", routing_key='test')
        channel.basic_publish(exchange='test', routing_key='test',  properties=pika.BasicProperties(
            headers={'key': 'value'}
        ),
                              body=b'Test message.')
        connection.close()

        return jsonify({"song": "Despacito", "artist": "Luis Fonsi"})

    PORT = 9090
    app.run(host='0.0.0.0', port=PORT, debug=True)
