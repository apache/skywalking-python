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

from threading import Lock, Thread

import time
from typing import Set
from skywalking import config
from skywalking.log import logger

import asyncio


class SamplingServiceBase:

    def __init__(self):
        self.sampling_factor = 0

    @property
    def reset_sampling_factor_interval(self) -> int:
        return 3

    @property
    def can_sampling(self):
        return self.sampling_factor < config.sample_n_per_3_secs

    def _try_sampling(self) -> bool:
        if self.can_sampling:
            self._incr_sampling_factor()
            return True
        logger.debug('%s try_sampling return false, sampling_factor: %d', self.__class__.__name__, self.sampling_factor)
        return False

    def _set_sampling_factor(self, val: int):
        logger.debug('Set sampling factor to %d', val)
        self.sampling_factor = val

    def _incr_sampling_factor(self):
        self.sampling_factor += 1


class SamplingService(Thread, SamplingServiceBase):

    def __init__(self):
        Thread.__init__(self, name='SamplingService', daemon=True)
        SamplingServiceBase.__init__(self)
        self.lock = Lock()

    def run(self):
        logger.debug('Started sampling service sampling_n_per_3_secs: %d', config.sample_n_per_3_secs)
        while True:
            self.reset_sampling_factor()
            time.sleep(self.reset_sampling_factor_interval)

    def try_sampling(self) -> bool:
        with self.lock:
            return super()._try_sampling()

    def force_sampled(self) -> None:
        with self.lock:
            super()._incr_sampling_factor()

    def reset_sampling_factor(self) -> None:
        with self.lock:
            super()._set_sampling_factor(0)


class SamplingServiceAsync(SamplingServiceBase):

    def __init__(self):
        super().__init__()
        self.strong_ref_set: Set[asyncio.Task[None]] = set()

    async def start(self):
        logger.debug('Started async sampling service sampling_n_per_3_secs: %d', config.sample_n_per_3_secs)
        while True:
            await self.reset_sampling_factor()
            await asyncio.sleep(self.reset_sampling_factor_interval)

    def try_sampling(self) -> bool:
        return super()._try_sampling()

    def force_sampled(self):
        super()._incr_sampling_factor()

    async def reset_sampling_factor(self):
        super()._set_sampling_factor(0)
