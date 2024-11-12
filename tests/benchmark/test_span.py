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

from typing import Any
from skywalking.trace.context import NoopContext
from skywalking.trace.span import NoopSpan


def test_noopspan_1000(benchmark: Any):
    result = benchmark(lambda: [NoopSpan(NoopContext()) for _ in range(1000)])
    assert result


def test_noopspan_40000(benchmark: Any):
    result = benchmark(lambda: [NoopSpan(NoopContext()) for _ in range(40000)])
    assert result


def test_noopspan_200k(benchmark: Any):
    result = benchmark(
        lambda: [NoopSpan(NoopContext()) for _ in range(200000)])
    assert result
