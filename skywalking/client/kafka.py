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

import os
import ast
from skywalking.loggings import logger

from skywalking import config
from skywalking.client import ServiceManagementClient, TraceSegmentReportService
from skywalking.protocol.common.Common_pb2 import KeyStringValuePair
from skywalking.protocol.management.Management_pb2 import InstancePingPkg, InstanceProperties

from kafka import KafkaProducer

kafka_configs = {}


def __init_kafka_configs():
    kafka_configs["bootstrap_servers"] = config.kafka_bootstrap_servers.split(",")
    # process all kafka configs in env
    kafka_keys = [key for key in os.environ.keys() if key.startswith("SW_KAFKA_REPORTER_CONFIG_")]
    for kafka_key in kafka_keys:
        key = kafka_key[25:]
        val = os.environ.get(kafka_key)

        if val is not None:
            if val.isnumeric():
                val = int(val)
            elif val in ["True", "False"]:
                val = ast.literal_eval(val)
        else:
            continue

        # check if the key was already set
        if kafka_configs.get(key) is None:
            kafka_configs[key] = val
        else:
            raise KafkaConfigDuplicated(key)


__init_kafka_configs()


class KafkaServiceManagementClient(ServiceManagementClient):
    def __init__(self):
        logger.debug("kafka reporter configs: %s", kafka_configs)
        self.producer = KafkaProducer(**kafka_configs)
        self.topic_key_register = "register-"
        self.topic = config.kafka_topic_management

        self.send_instance_props()

    def send_instance_props(self):
        instance = InstanceProperties(
            service=config.service_name,
            serviceInstance=config.service_instance,
            properties=[KeyStringValuePair(key='language', value='Python')],
        )

        key = bytes(self.topic_key_register + instance.serviceInstance, encoding='utf-8')
        value = bytes(instance.SerializeToString())
        self.producer.send(topic=self.topic, key=key, value=value)

    def send_heart_beat(self):
        logger.debug(
            'service heart beats, [%s], [%s]',
            config.service_name,
            config.service_instance,
        )

        instance_ping_pkg = InstancePingPkg(
            service=config.service_name,
            serviceInstance=config.service_instance,
        )

        key = bytes(instance_ping_pkg.serviceInstance, encoding="utf-8")
        value = bytes(instance_ping_pkg.SerializeToString())
        future = self.producer.send(topic=self.topic, key=key, value=value)
        res = future.get(timeout=10)
        logger.debug('heartbeat response: %s', res)


class KafkaTraceSegmentReportService(TraceSegmentReportService):
    def __init__(self):
        self.producer = KafkaProducer(**kafka_configs)
        self.topic = config.kafka_topic_segment

    def report(self, generator):
        for segment in generator:
            key = bytes(segment.traceSegmentId, encoding="utf-8")
            value = bytes(segment.SerializeToString())
            self.producer.send(topic=self.topic, key=key, value=value)


class KafkaConfigDuplicated(Exception):
    def __init__(self, key):
        self.key = key
