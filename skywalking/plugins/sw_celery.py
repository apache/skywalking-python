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

from skywalking import Layer, Component, config
from skywalking.trace.carrier import Carrier
from skywalking.trace.context import get_context
from skywalking.trace.tags import TagMqBroker, TagCeleryParameters

link_vector = ['https://docs.celeryproject.org']
# TODO: Celery is missing plugin test
support_matrix = {
    'celery': {
        '>=3.6': ['5.1']
    }
}
note = """The celery server running with "celery -A ..." should be run with the HTTP protocol
as it uses multiprocessing by default which is not compatible with the gRPC protocol implementation
in SkyWalking currently. Celery clients can use whatever protocol they want."""


def install():
    from urllib.parse import urlparse
    from celery import Celery

    def send_task(self, name, args=None, kwargs=None, **options):
        # NOTE: Lines commented out below left for documentation purposes if sometime in the future exchange / queue
        # names are wanted. Currently these do not match between producer and consumer so would need some work.

        broker_url = self.conf['broker_url']
        # exchange = options['exchange']
        # queue = options['routing_key']
        # op = 'celery/{}/{}/{}'.format(exchange or '', queue or '', name)
        op = f'celery/{name}'

        if broker_url:
            url = urlparse(broker_url)
            peer = f'{url.hostname}:{url.port}'
        else:
            peer = '???'

        with get_context().new_exit_span(op=op, peer=peer, component=Component.Celery) as span:
            span.layer = Layer.MQ

            span.tag(TagMqBroker(broker_url))
            # span.tag(TagMqTopic(exchange))
            # span.tag(TagMqQueue(queue))

            if config.celery_parameters_length:
                params = f'*{args}, **{kwargs}'[:config.celery_parameters_length]
                span.tag(TagCeleryParameters(params))

            options = {**options}
            headers = options.get('headers')
            headers = {**headers} if headers else {}
            options['headers'] = headers

            for item in span.inject():
                headers[item.key] = item.val

            return _send_task(self, name, args, kwargs, **options)

    _send_task = Celery.send_task
    Celery.send_task = send_task

    def task_from_fun(self, _fun, name=None, **options):
        def fun(*args, **kwargs):
            req = task.request_stack.top
            # di = req.get('delivery_info')
            # exchange = di and di.get('exchange')
            # queue = di and di.get('routing_key')
            # op = 'celery/{}/{}/{}'.format(exchange or '', queue or '', name)
            op = f'celery/{name}'
            carrier = Carrier()

            for item in carrier:
                val = req.get(item.key)

                if val:
                    item.val = val

            context = get_context()
            origin = req.get('origin')

            if origin:
                span = context.new_entry_span(op=op, carrier=carrier)
                span.peer = origin.split('@', 1)[-1]
            else:
                span = context.new_local_span(op=op)

            with span:
                span.layer = Layer.MQ
                span.component = Component.Celery

                span.tag(TagMqBroker(task.app.conf['broker_url']))
                # span.tag(TagMqTopic(exchange))
                # span.tag(TagMqQueue(queue))

                if config.celery_parameters_length:
                    params = f'*{args}, **{kwargs}'[:config.celery_parameters_length]
                    span.tag(TagCeleryParameters(params))

                return _fun(*args, **kwargs)

        name = name or self.gen_task_name(_fun.__name__, _fun.__module__)
        task = _task_from_fun(self, fun, name, **options)

        return task

    _task_from_fun = Celery._task_from_fun
    Celery._task_from_fun = task_from_fun
