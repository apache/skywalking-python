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

import ast
import os
import asyncio
from asyncio import Event

from aiokafka import AIOKafkaProducer

from skywalking import config
from skywalking.client import MeterReportServiceAsync, ServiceManagementClientAsync, \
    TraceSegmentReportServiceAsync, LogDataReportServiceAsync
from skywalking.loggings import logger, logger_debug_enabled
from skywalking.protocol.language_agent.Meter_pb2 import MeterDataCollection
from skywalking.protocol.management.Management_pb2 import InstancePingPkg, InstanceProperties

kafka_configs = {}


def __init_kafka_configs():
    global kafka_configs
    kafka_configs['bootstrap_servers'] = config.kafka_bootstrap_servers.split(',')
    # process all kafka configs in env
    kafka_keys = [key for key in os.environ.keys() if key.startswith('SW_KAFKA_REPORTER_CONFIG_')]
    for kafka_key in kafka_keys:
        key = kafka_key[25:]
        val = os.environ.get(kafka_key)

        if val is not None:
            if val.isnumeric():
                val = int(val)
            elif val in ['True', 'False']:
                val = ast.literal_eval(val)
        else:
            continue

        # check if the key was already set
        if kafka_configs.get(key) is None:
            kafka_configs[key] = val
        else:
            raise KafkaConfigDuplicated(key)


__init_kafka_configs()


class KafkaServiceManagementClientAsync(ServiceManagementClientAsync):
    def __init__(self):
        super().__init__()
        self.instance_properties = self.get_instance_properties_proto()

        if logger_debug_enabled:
            logger.debug('kafka reporter configs: %s', kafka_configs)
        # self.producer = KafkaProducer(**kafka_configs)
        self.producer = AIOKafkaProducer(**kafka_configs)
        # We can not start AIOKafkaProducer in sync code
        # So we use a event to make sure producer is started on demand
        self.__producer_start_event = Event()
        self.topic_key_register = 'register-'
        self.topic = config.kafka_topic_management

        asyncio.run_coroutine_threadsafe(self.send_instance_props(), loop=asyncio.get_event_loop())

    async def send_instance_props(self):
        if not self.__producer_start_event.is_set():
            await self.producer.start()
            self.__producer_start_event.set()

        instance = InstanceProperties(
            service=config.agent_name,
            serviceInstance=config.agent_instance_name,
            properties=self.instance_properties,
        )

        key = bytes(self.topic_key_register + instance.serviceInstance, encoding='utf-8')
        value = instance.SerializeToString()
        await self.producer.send_and_wait(topic=self.topic, key=key, value=value)

    async def send_heart_beat(self):
        if not self.__producer_start_event.is_set():
            await self.producer.start()
            self.__producer_start_event.set()

        await self.refresh_instance_props()

        if logger_debug_enabled:
            logger.debug(
                'service heart beats, [%s], [%s]',
                config.agent_name,
                config.agent_instance_name,
            )

        instance_ping_pkg = InstancePingPkg(
            service=config.agent_name,
            serviceInstance=config.agent_instance_name,
        )

        key = bytes(instance_ping_pkg.serviceInstance, encoding='utf-8')
        value = instance_ping_pkg.SerializeToString()
        future = await self.producer.send_and_wait(topic=self.topic, key=key, value=value)
        if logger_debug_enabled:
            logger.debug('heartbeat response: %s', future)


class KafkaTraceSegmentReportServiceAsync(TraceSegmentReportServiceAsync):
    def __init__(self):
        self.producer = AIOKafkaProducer(**kafka_configs)
        # We can not start AIOKafkaProducer in sync code
        # So we use a event to make sure producer is started on demand
        self.__producer_start_event = Event()
        self.topic = config.kafka_topic_segment

    async def report(self, generator):
        if not self.__producer_start_event.is_set():
            await self.producer.start()
            self.__producer_start_event.set()

        async for segment in generator:
            key = bytes(segment.traceSegmentId, encoding='utf-8')
            value = segment.SerializeToString()
            await self.producer.send_and_wait(topic=self.topic, key=key, value=value)


class KafkaLogDataReportServiceAsync(LogDataReportServiceAsync):
    def __init__(self):
        self.producer = AIOKafkaProducer(**kafka_configs)
        # We can not start AIOKafkaProducer in sync code
        # So we use a event to make sure producer is started on demand
        self.__producer_start_event = Event()
        self.topic = config.kafka_topic_log

    async def report(self, generator):
        if not self.__producer_start_event.is_set():
            await self.producer.start()
            self.__producer_start_event.set()

        async for log_data in generator:
            key = bytes(log_data.traceContext.traceSegmentId, encoding='utf-8')
            value = log_data.SerializeToString()
            await self.producer.send_and_wait(topic=self.topic, key=key, value=value)


class KafkaMeterDataReportServiceAsync(MeterReportServiceAsync):
    def __init__(self):
        self.producer = AIOKafkaProducer(**kafka_configs)
        # We can not start AIOKafkaProducer in sync code
        # So we use a event to make sure producer is started on demand
        self.__producer_start_event = Event()
        self.topic = config.kafka_topic_meter

    async def report(self, generator):
        if not self.__producer_start_event.is_set():
            await self.producer.start()
            self.__producer_start_event.set()

        collection = MeterDataCollection()
        collection.meterData.extend([data async for data in generator])
        key = bytes(config.agent_instance_name, encoding='utf-8')
        value = collection.SerializeToString()
        await self.producer.send_and_wait(topic=self.topic, key=key, value=value)


class KafkaConfigDuplicated(Exception):
    def __init__(self, key):
        self.key = key
