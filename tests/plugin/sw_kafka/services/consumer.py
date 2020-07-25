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

    topic = "skywalking"
    server_list = ["kafka-server:9092"]
    group_id = "skywalking"
    client_id = "0"

    from kafka import KafkaConsumer
    from kafka import TopicPartition
    consumer = KafkaConsumer(group_id=group_id,
                             client_id=client_id,
                             bootstrap_servers=server_list)
    partition = TopicPartition(topic, int(client_id))
    consumer.assign([partition])
    for msg in consumer:
        print(msg)
