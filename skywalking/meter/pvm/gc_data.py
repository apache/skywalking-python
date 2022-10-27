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

import gc
import time

from skywalking.meter.pvm.data_source import DataSource


class GCDataSource(DataSource):
    def gc_g0_generator(self):
        while (True):
            yield gc.get_stats()[0]['collected']

    def gc_g1_generator(self):
        while (True):
            yield gc.get_stats()[1]['collected']

    def gc_g2_generator(self):
        while (True):
            yield gc.get_stats()[2]['collected']

    def gc_time_generator(self):
        self.gc_time = 0

        def gc_callback(phase, info):
            if phase == 'start':
                self.start_time = time.time()
            elif phase == 'stop':
                self.gc_time = (time.time() - self.start_time) * 1000

        if hasattr(gc, 'callbacks'):
            gc.callbacks.append(gc_callback)

        while (True):
            yield self.gc_time
