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

from skywalking.sampling.sampling_service import SamplingService, SamplingServiceAsync


class TestSampling(unittest.TestCase):

    def test_try_sampling(self):
        from skywalking import config

        config.sample_n_per_3_secs = 2
        sampling_service = SamplingService()
        assert sampling_service.try_sampling()
        assert sampling_service.try_sampling()
        assert not sampling_service.try_sampling()

    def test_force_sampled(self):

        from skywalking import config

        config.sample_n_per_3_secs = 1
        sampling_service = SamplingService()
        assert sampling_service.try_sampling()
        sampling_service.force_sampled()
        assert sampling_service.sampling_factor == 2

    def test_reset_sampling_factor(self):
        from skywalking import config

        config.sample_n_per_3_secs = 1
        sampling_service = SamplingService()
        assert sampling_service.try_sampling()
        assert not sampling_service.try_sampling()
        sampling_service.reset_sampling_factor()
        assert sampling_service.try_sampling()


class TestSamplingAsync(unittest.IsolatedAsyncioTestCase):

    async def test_try_sampling(self):
        from skywalking import config

        config.sample_n_per_3_secs = 2
        sampling_service = SamplingServiceAsync()
        assert sampling_service.try_sampling()
        assert sampling_service.try_sampling()
        assert not sampling_service.try_sampling()

    async def test_force_sampled(self):

        from skywalking import config

        config.sample_n_per_3_secs = 1
        sampling_service = SamplingServiceAsync()
        assert sampling_service.try_sampling()
        sampling_service.force_sampled()
        assert sampling_service.sampling_factor == 2

    async def test_reset_sampling_factor(self):
        from skywalking import config

        config.sample_n_per_3_secs = 1
        sampling_service = SamplingServiceAsync()
        assert sampling_service.try_sampling()
        assert not sampling_service.try_sampling()
        await sampling_service.reset_sampling_factor()
        assert sampling_service.try_sampling()


if __name__ == '__main__':
    unittest.main()
