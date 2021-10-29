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

from skywalking import Layer, Component
from skywalking import config
from skywalking.trace.carrier import Carrier
from skywalking.trace.context import get_context
from skywalking.trace.tags import TagMqBroker, TagMqTopic

link_vector = ['https://kafka-python.readthedocs.io']

support_matrix = {
    'kafka-python': {
        '>=3.6': ['2.0']
    }
}
note = """"""


def install():
    from kafka import KafkaProducer
    from kafka import KafkaConsumer

    _send = KafkaProducer.send
    __poll_once = KafkaConsumer._poll_once
    KafkaProducer.send = _sw_send_func(_send)
    KafkaConsumer._poll_once = _sw__poll_once_func(__poll_once)


def _sw__poll_once_func(__poll_once):
    def _sw__poll_once(this, timeout_ms, max_records, update_offsets=True):
        res = __poll_once(this, timeout_ms, max_records, update_offsets=update_offsets)
        if res:
            brokers = ';'.join(this.config['bootstrap_servers'])
            context = get_context()
            topics = ';'.join(this._subscription.subscription
                              or [t.topic for t in this._subscription._user_assignment])

            with context.new_entry_span(
                    op=f"Kafka/{topics}/Consumer/{this.config['group_id'] or ''}") as span:
                for consumer_records in res.values():
                    for record in consumer_records:
                        carrier = Carrier()
                        for item in carrier:
                            for header in record.headers:
                                if item.key == header[0]:
                                    item.val = str(header[1])

                        span.extract(carrier)
                    span.tag(TagMqBroker(brokers))
                    span.tag(TagMqTopic(topics))
                    span.layer = Layer.MQ
                    span.component = Component.KafkaConsumer

        return res

    return _sw__poll_once


def _sw_send_func(_send):
    def _sw_send(this, topic, value=None, key=None, headers=None, partition=None, timestamp_ms=None):
        # ignore trace & log reporter - skywalking self request
        if config.protocol == 'kafka' and config.kafka_topic_segment == topic \
                or config.kafka_topic_log == topic \
                or config.kafka_topic_management == topic:
            return _send(this, topic, value=value, key=key, headers=headers, partition=partition,
                         timestamp_ms=timestamp_ms)

        peer = ';'.join(this.config['bootstrap_servers'])
        context = get_context()
        with context.new_exit_span(op=f'Kafka/{topic}/Producer' or '/', peer=peer,
                                   component=Component.KafkaProducer) as span:
            carrier = span.inject()
            span.layer = Layer.MQ

            if headers is None:
                headers = []
            for item in carrier:
                headers.append((item.key, item.val.encode('utf-8')))

            res = _send(this, topic, value=value, key=key, headers=headers, partition=partition,
                        timestamp_ms=timestamp_ms)
            span.tag(TagMqBroker(peer))
            span.tag(TagMqTopic(topic))

            return res

    return _sw_send
