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

link_vector = ['https://pika.readthedocs.io']
support_matrix = {
    'pika': {
        '>=3.6': ['1.2']
    }
}
note = """"""


def install():
    from pika.channel import Channel
    from pika.adapters.blocking_connection import BlockingChannel

    Channel.basic_publish = _sw_basic_publish_func(Channel.basic_publish)
    Channel._on_deliver = _sw__on_deliver_func(Channel._on_deliver)
    BlockingChannel.basic_consume = _sw_blocking_basic_consume_func(BlockingChannel.basic_consume)
    BlockingChannel.basic_get = _sw_blocking_basic_get_func(BlockingChannel.basic_get)
    BlockingChannel.consume = _sw_blocking_consume_func(BlockingChannel.consume)


def _sw_basic_publish_func(_basic_publish):
    def _sw_basic_publish(this, exchange,
                          routing_key,
                          body,
                          properties=None,
                          mandatory=False):
        peer = f'{this.connection.params.host}:{this.connection.params.port}'
        context = get_context()
        import pika
        with context.new_exit_span(op=f'RabbitMQ/Topic/{exchange}/Queue/{routing_key}/Producer' or '/',
                                   peer=peer, component=Component.RabbitmqProducer) as span:
            carrier = span.inject()
            span.layer = Layer.MQ
            properties = pika.BasicProperties() if properties is None else properties

            if properties.headers is None:
                properties.headers = {}
            for item in carrier:
                properties.headers[item.key] = item.val

            res = _basic_publish(this, exchange,
                                 routing_key,
                                 body,
                                 properties=properties,
                                 mandatory=mandatory)
            span.tag(TagMqBroker(peer))
            span.tag(TagMqTopic(exchange))
            span.tag(TagMqQueue(routing_key))

            return res

    return _sw_basic_publish


def _sw__on_deliver_func(__on_deliver):
    from pika.adapters.blocking_connection import BlockingChannel

    def _sw__on_deliver(this, method_frame, header_frame, body):
        peer = f'{this.connection.params.host}:{this.connection.params.port}'
        consumer_tag = method_frame.method.consumer_tag

        # The following is a special case for one type of channel to allow any exit spans to be linked properly to the
        # incoming segment. Otherwise, if we create the span here the span ends before any oser callbacks are called and
        # so any new spans will not be linked to the incoming message.

        defer_span = False

        try:  # future-proofing if object structure changes
            if consumer_tag not in this._cancelled and consumer_tag in this._consumers:
                consumer = this._consumers[consumer_tag]

                if isinstance(consumer.__self__, BlockingChannel):
                    method_frame.method._sw_peer = peer
                    defer_span = True

        except Exception:
            pass

        if defer_span:
            return __on_deliver(this, method_frame, header_frame, body)

        context = get_context()
        exchange = method_frame.method.exchange
        routing_key = method_frame.method.routing_key
        carrier = Carrier()
        for item in carrier:
            try:
                if item.key in header_frame.properties.headers:
                    item.val = header_frame.properties.headers[item.key]
            except TypeError:
                pass

        with context.new_entry_span(op='RabbitMQ/Topic/' + exchange + '/Queue/' + routing_key
                                       + '/Consumer' or '', carrier=carrier) as span:
            span.layer = Layer.MQ
            span.component = Component.RabbitmqConsumer
            __on_deliver(this, method_frame, header_frame, body)
            span.tag(TagMqBroker(peer))
            span.tag(TagMqTopic(exchange))
            span.tag(TagMqQueue(routing_key))

    return _sw__on_deliver


def _sw_callback_func(callback):
    def _sw_callback(this, method, properties, body):
        peer = getattr(method, '_sw_peer', None)

        if peer is None:
            params = getattr(getattr(this.connection, '_impl', None), 'params', None)
            peer = '<unavailable>' if params is None else f'{params.host}:{params.port}'

        context = get_context()
        exchange = method.exchange
        routing_key = method.routing_key
        carrier = Carrier()
        for item in carrier:
            try:
                if item.key in properties.headers:
                    item.val = properties.headers[item.key]
            except TypeError:
                pass

        with context.new_entry_span(op='RabbitMQ/Topic/' + exchange + '/Queue/' + routing_key
                                    + '/Consumer' or '', carrier=carrier) as span:
            span.layer = Layer.MQ
            span.component = Component.RabbitmqConsumer
            res = callback(this, method, properties, body)
            span.tag(TagMqBroker(peer))
            span.tag(TagMqTopic(exchange))
            span.tag(TagMqQueue(routing_key))

        return res

    return _sw_callback


def _sw_blocking_basic_consume_func(func):
    def _sw_basic_consume(this, queue, on_message_callback, *args, **kwargs):
        return func(this, queue, _sw_callback_func(on_message_callback), *args, **kwargs)

    return _sw_basic_consume


def _sw_blocking_basic_get_func(func):
    def _sw_basic_get(this, queue, *args, **kwargs):
        method, properties, body = func(this, queue, *args, **kwargs)

        if method is not None:
            _sw_callback_func(lambda *a: None)(this, method, properties, body)

        return method, properties, body

    return _sw_basic_get


def _sw_blocking_consume_func(func):
    def _sw_consume(this, queue, *args, **kwargs):
        for method, properties, body in func(this, queue, *args, **kwargs):
            if method is not None:
                _sw_callback_func(lambda *a: None)(this, method, properties, body)

            yield method, properties, body

    return _sw_consume
