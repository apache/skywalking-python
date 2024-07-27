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
from skywalking.trace.carrier import Carrier
from skywalking.trace.context import get_context
from skywalking.trace.tags import TagMqTopic, TagMqBroker

link_vector = ['https://github.com/apache/pulsar-client-python']
support_matrix = {
    'pulsar-client': {
        '>=3.8': ['3.3.0']
    }
}
note = """"""


def install():
    from pulsar import Producer
    from pulsar import Consumer
    from pulsar import Client

    __init = Client.__init__
    _send = Producer.send
    _receive = Consumer.receive
    _peer = ''

    def get_peer():
        return _peer

    def set_peer(value):
        nonlocal _peer
        _peer = value

    def _sw_init(self, service_url, *args, **kwargs):
        __init(self, service_url, *args, **kwargs)
        set_peer(service_url)

    def _sw_send_func(_send):
        def _sw_send(this, content,
                     properties=None,
                     partition_key=None,
                     sequence_id=None,
                     replication_clusters=None,
                     disable_replication=False,
                     event_timestamp=None,
                     deliver_at=None,
                     deliver_after=None,
                     ):
            topic = this._producer.topic().split('/')[-1]
            with get_context().new_exit_span(op=f'Pulsar/Topic/{topic}/Producer', peer=get_peer(),
                                             component=Component.PulsarProducer) as span:
                span.tag(TagMqTopic(topic))
                span.tag(TagMqBroker(get_peer()))
                span.layer = Layer.MQ

                carrier = span.inject()
                if properties is None:
                    properties = {}
                for item in carrier:
                    properties[item.key] = item.val

                return _send(this, content, properties=properties, partition_key=partition_key,
                             sequence_id=sequence_id, replication_clusters=replication_clusters,
                             disable_replication=disable_replication, event_timestamp=event_timestamp,
                             deliver_at=deliver_at, deliver_after=deliver_after)

        return _sw_send

    def _sw_receive_func(_receive):
        def _sw_receive(this, timeout_millis=None):
            res = _receive(this, timeout_millis=timeout_millis)
            if res:
                topic = res.topic_name().split('/')[-1]
                properties = res.properties()
                carrier = Carrier()
                for item in carrier:
                    if item.key in properties.keys():
                        val = res.properties().get(item.key)
                        if val is not None:
                            item.val = val

                with get_context().new_entry_span(op=f'Pulsar/Topic/{topic}/Consumer', carrier=carrier) as span:
                    span.tag(TagMqTopic(topic))
                    span.tag(TagMqBroker(get_peer()))
                    span.layer = Layer.MQ
                    span.component = Component.PulsarConsumer
            return res

        return _sw_receive

    Client.__init__ = _sw_init
    Producer.send = _sw_send_func(_send)
    Consumer.receive = _sw_receive_func(_receive)
