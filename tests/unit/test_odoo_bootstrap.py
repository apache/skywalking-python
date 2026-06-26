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
import unittest

from skywalking import config
from skywalking.bootstrap import odoo


class TestOdooBootstrap(unittest.TestCase):
    def setUp(self):
        self.environ = os.environ.copy()
        self.original_protocol = config.agent_protocol
        self.original_name = config.agent_name
        self.original_namespace = config.agent_namespace
        self.original_backend = config.agent_collector_backend_services
        self.original_tls = config.agent_force_tls
        self.started = []
        self.original_start_agent = odoo._start_agent
        odoo._start_agent = lambda: self.started.append(True)

    def tearDown(self):
        os.environ.clear()
        os.environ.update(self.environ)
        config.agent_protocol = self.original_protocol
        config.agent_name = self.original_name
        config.agent_namespace = self.original_namespace
        config.agent_collector_backend_services = self.original_backend
        config.agent_force_tls = self.original_tls
        odoo._start_agent = self.original_start_agent

    def test_maybe_start_noops_without_agent_name(self):
        os.environ.pop('SW_AGENT_NAME', None)
        os.environ['SW_AGENT_COLLECTOR_BACKEND_SERVICES'] = 'http://oap:12800'

        self.assertFalse(odoo.maybe_start())

        self.assertEqual([], self.started)

    def test_maybe_start_noops_without_backend(self):
        os.environ['SW_AGENT_NAME'] = 'odoo-service'
        os.environ.pop('SW_AGENT_COLLECTOR_BACKEND_SERVICES', None)

        self.assertFalse(odoo.maybe_start())

        self.assertEqual([], self.started)

    def test_maybe_start_uses_sw_agent_name_as_service_name(self):
        os.environ['SW_AGENT_NAME'] = 'odoo-service'
        os.environ['SW_AGENT_COLLECTOR_BACKEND_SERVICES'] = 'http://oap:12800'
        config.agent_namespace = 'unexpected-namespace'

        self.assertTrue(odoo.maybe_start())

        self.assertEqual('http', config.agent_protocol)
        self.assertEqual('odoo-service', config.agent_name)
        self.assertEqual('unexpected-namespace', config.agent_namespace)
        self.assertEqual('oap:12800', config.agent_collector_backend_services)
        self.assertFalse(config.agent_force_tls)
        self.assertEqual([True], self.started)

    def test_maybe_start_accepts_https_backend(self):
        os.environ['SW_AGENT_NAME'] = 'odoo-service'
        os.environ['SW_AGENT_COLLECTOR_BACKEND_SERVICES'] = 'https://oap.example.com:12800'

        self.assertTrue(odoo.maybe_start())

        self.assertEqual('oap.example.com:12800', config.agent_collector_backend_services)
        self.assertTrue(config.agent_force_tls)
        self.assertEqual([True], self.started)

    def test_maybe_start_returns_false_when_agent_start_fails(self):
        os.environ['SW_AGENT_NAME'] = 'odoo-service'
        os.environ['SW_AGENT_COLLECTOR_BACKEND_SERVICES'] = 'http://oap:12800'

        def fail_start():
            raise RuntimeError('agent failed')

        odoo._start_agent = fail_start

        self.assertFalse(odoo.maybe_start())

    def test_maybe_start_strips_empty_values(self):
        os.environ['SW_AGENT_NAME'] = '   '
        os.environ['SW_AGENT_COLLECTOR_BACKEND_SERVICES'] = ' http://oap:12800 '

        self.assertFalse(odoo.maybe_start())

        self.assertEqual([], self.started)


if __name__ == '__main__':
    unittest.main()
