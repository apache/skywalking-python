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

from skywalking import config, agent

if __name__ == '__main__':
    config.service_name = 'consumer'
    config.logging_level = 'INFO'
    agent.start()

    import pika

    parameters = (pika.URLParameters("amqp://admin:admin@rabbitmq-server:5672/%2F"))

    connection = pika.BlockingConnection(parameters)

    channel = connection.channel()
    channel.queue_declare("test")
    channel.exchange_declare("test")
    channel.queue_bind(exchange='test', queue="test", routing_key='test')
    for method_frame, properties, body in channel.consume('test'):
        # Display the message parts and acknowledge the message
        print(method_frame, properties, body)
        channel.basic_ack(method_frame.delivery_tag)

        # Escape out of the loop after 10 messages
        if method_frame.delivery_tag == 10:
            break

    try:
        # Loop so we can communicate with RabbitMQ
        connection.ioloop.start()
    except KeyboardInterrupt:
        # Gracefully close the connection
        connection.close()
        # Loop until we're fully closed, will stop on its own
        connection.ioloop.start()
