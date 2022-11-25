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
from skywalking.trace.tags import TagMqBroker, TagMqTopic, TagMqQueue

link_vector = ['https://www.confluent.io/']
support_matrix = {
    'confluent_kafka': {
        '>=3.7': ['1.5.0', '1.7.0', '1.8.2']
    }
}
note = """"""


def install():
    import wrapt  # Producer and Consumer are read-only C extension objects so they need to be proxied
    import confluent_kafka

    class ProxyProducer(wrapt.ObjectProxy):
        def __init__(self, *args, **kwargs):
            servers = kwargs.get('bootstrap.servers', (args[0].get('bootstrap.servers') if len(args) else False) or '<unavailable>')

            self._self_peer = servers if isinstance(servers, str) else ';'.join(servers)
            self._self_producer = _producer(*args, **kwargs)

            wrapt.ObjectProxy.__init__(self, self._self_producer)

        def produce(self, topic, *args, **kwargs):
            largs = len(args)
            # value = args[0] if largs else kwargs.get('value')
            key = args[1] if largs >= 2 else kwargs.get('key')
            headers = args[6] if largs >= 7 else kwargs.get('headers')
            headers = {} if headers is None else dict(headers)
            peer = self._self_peer
            context = get_context()

            if isinstance(key, bytes):
                key = key.decode('utf-8')

            with context.new_exit_span(op=f'Kafka/{topic}/{key or ""}/Producer' or '/', peer=peer,
                                       component=Component.KafkaProducer) as span:
                carrier = span.inject()
                span.layer = Layer.MQ

                span.tag(TagMqBroker(peer))
                span.tag(TagMqTopic(topic))

                if key is not None:
                    span.tag(TagMqQueue(key))

                for item in carrier:
                    headers[item.key] = item.val.encode('utf-8')

                if largs >= 7:
                    args = args[:6] + (headers,) + args[7:]
                else:
                    kwargs = {**kwargs, 'headers': headers}

                return _producer.produce(self._self_producer, topic, *args, **kwargs)

    _producer = confluent_kafka.Producer
    confluent_kafka.Producer = ProxyProducer

    class ProxyConsumer(wrapt.ObjectProxy):
        def __init__(self, *args, **kwargs):
            servers = kwargs.get('bootstrap.servers', (args[0].get('bootstrap.servers') if len(args) else False) or '<unavailable>')
            group_id = kwargs.get('group.id', (args[0].get('group.id') if len(args) else False) or '<no group ID>')

            self._self_peer = servers if isinstance(servers, str) else ';'.join(servers)
            self._self_group_id = group_id
            self._self_consumer = _consumer(*args, **kwargs)

            wrapt.ObjectProxy.__init__(self, self._self_consumer)

        def message(self, msg):
            if msg is not None and not msg.error():
                context = get_context()
                topic = msg.topic()
                key = msg.key()
                headers = dict(msg.headers() or ())

                if isinstance(key, bytes):
                    key = key.decode('utf-8')

                with context.new_entry_span(
                        op=f"Kafka/{topic or ''}/{key or ''}/Consumer/{self._self_group_id}") as span:

                    span.layer = Layer.MQ
                    span.component = Component.KafkaConsumer
                    carrier = Carrier()

                    for item in carrier:
                        val = headers.get(item.key)

                        if val is not None:
                            item.val = val.decode('utf-8')

                    span.extract(carrier)
                    span.tag(TagMqBroker(self._self_peer))
                    span.tag(TagMqTopic(topic))

                    if key is not None:
                        span.tag(TagMqQueue(key))

            return msg

        def poll(self, *args, **kwargs):
            return self.message(_consumer.poll(self._self_consumer, *args, **kwargs))

        def consume(self, *args, **kwargs):
            msgs = _consumer.consume(self._self_consumer, *args, **kwargs)

            for msg in msgs:
                self.message(msg)

            return msgs

    _consumer = confluent_kafka.Consumer
    confluent_kafka.Consumer = ProxyConsumer
