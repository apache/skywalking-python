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

from packaging import version

from skywalking.plugins import check
from skywalking.utils.comparator import operators


class TestVersionCheck(unittest.TestCase):
    def test_operators(self):
        # <
        f = operators.get('<')
        v1 = version.parse('1.0.0')
        v2 = version.parse('1.0.1')
        assert f(v1, v2) is True
        assert f(v2, v1) is False

        v2 = version.parse('1.0.0')
        assert f(v1, v2) is False

        # <=
        f = operators.get('<=')
        v1 = version.parse('1.0')
        v2 = version.parse('1.0')
        assert f(v1, v2) is True

        v2 = version.parse('1.1.0')
        assert f(v1, v2) is True
        assert f(v2, v1) is False

        # =
        f = operators.get('==')
        v1 = version.parse('1.0.0')
        v2 = version.parse('1.0.0')
        assert f(v1, v2) is True

        v2 = version.parse('1.0.1')
        assert f(v1, v2) is False

        # >=
        f = operators.get('>=')
        v1 = version.parse('1.0.0')
        v2 = version.parse('1.0.0')
        assert f(v1, v2) is True

        v2 = version.parse('1.0.1')
        assert f(v1, v2) is False
        assert f(v2, v1) is True

        # >
        f = operators.get('>')
        v1 = version.parse('1.0.0')
        v2 = version.parse('1.0.1')
        assert f(v1, v2) is False
        assert f(v2, v1) is True

        v2 = version.parse('1.0.0')
        assert f(v1, v2) is False

        # !=
        f = operators.get('!=')
        v1 = version.parse('1.0.0')
        v2 = version.parse('1.0.1')
        assert f(v1, v2) is True

        v2 = version.parse('1.0.0')
        assert f(v1, v2) is False

    def test_version_check(self):
        current_version = version.parse('1.8.0')

        assert check('>1.1.0', current_version) is True
        assert check('>=1.0.0', current_version) is True
        assert check('<2.0.0', current_version) is True
        assert check('<=1.8.0', current_version) is True
        assert check('==1.8.0', current_version) is True
        assert check('!=1.6.0', current_version) is True

        assert check('>1.9.0', current_version) is False
        assert check('>=1.8.1', current_version) is False
        assert check('<1.8.0', current_version) is False
        assert check('<=1.7.0', current_version) is False
        assert check('==1.0.0', current_version) is False
        assert check('!=1.8.0', current_version) is False
