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

import unittest
from skywalking.utils.filter import sw_urlparse, sw_filter


class TestFilter(unittest.TestCase):
    def test_url_parse(self):
        self.assertEqual(sw_urlparse('http://localhost:8080').geturl(), 'http://localhost:8080')
        self.assertEqual(sw_urlparse('https://localhost:8080').geturl(), 'https://localhost:8080')
        self.assertEqual(sw_urlparse('http://user:password@localhost:8080').geturl(), 'http://localhost:8080')
        self.assertEqual(sw_urlparse('https://user:password@localhost:8080').geturl(), 'https://localhost:8080')
        self.assertEqual(sw_urlparse('ws://user:password@localhost:8080/ws').geturl(), 'ws://localhost:8080/ws')
        self.assertEqual(sw_urlparse('wss://user:password@localhost:8080/ws').geturl(), 'wss://localhost:8080/ws')

    def test_log_filter(self):
        from skywalking import config
        config.agent_log_reporter_safe_mode = True

        self.assertEqual(
            'user:password not in http://localhost:8080',
            sw_filter('user:password not in http://localhost:8080')
        )
        self.assertEqual(
            'user:password in http://localhost:8080',
            sw_filter('user:password in http://user:password@localhost:8080')
        )
        self.assertEqual(
            'http://localhost:8080 contains user:password',
            sw_filter('http://user:password@localhost:8080 contains user:password')
        )
        self.assertEqual(
            'DATETIMEhttp://localhost:8080 contains user:password',
            sw_filter('DATETIMEhttp://user:password@localhost:8080 contains user:password')
        )


if __name__ == '__main__':
    unittest.main()
