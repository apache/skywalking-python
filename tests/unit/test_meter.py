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
import random
import time

from skywalking.meter.counter import Counter, CounterMode
from skywalking.meter.histogram import Histogram
from skywalking.meter.gauge import Gauge
from skywalking.meter.meter import BaseMeter


class MockMeterService():
    def __init__(self):
        self.meter_map = {}

    def register(self, meter: BaseMeter):
        self.meter_map[meter.get_id().get_name()] = meter

    def get_meter(self, name: str):
        return self.meter_map.get(name)

    def transform(self, meter):
        meterdata = meter.transform()
        meterdata.service = 'service_name'
        meterdata.serviceInstance = 'service_instance'
        meterdata.timestamp = int(0)
        return meterdata


meter_service = MockMeterService()
BaseMeter.meter_service = meter_service

# picked empirically
tolerance = 5e-2


class TestMeter(unittest.TestCase):
    def test_counter(self):
        builder = Counter.Builder('c1', CounterMode.INCREMENT, (('k1', 'v1'), ('k2', 'v2')))
        builder.tag('k3', 'v3')
        c = builder.build()

        @Counter.increase(name='c1')
        def increase_by_one():
            # do nothing
            pass

        for i in range(1, 52):
            increase_by_one()
            self.assertEqual(i, c.count)
            meterdata = meter_service.transform(c)
            self.assertEqual(meterdata.singleValue.value, c.count)
            self.assertEqual(i, meterdata.singleValue.value)

    def test_counter_with_satement(self):
        builder = Counter.Builder('c2', CounterMode.INCREMENT)
        c = builder.build()

        ls = [i / 10 for i in range(10)]
        random.shuffle(ls)

        pre = 0
        for i in ls:
            with c.create_timer():
                time.sleep(i)

            meterdata = meter_service.transform(c)
            self.assertEqual(meterdata.singleValue.value, c.count)
            self.assertLess(abs(i - (meterdata.singleValue.value - pre)), tolerance)
            pre = meterdata.singleValue.value


    def test_counter_increase_decarator(self):
        builder = Counter.Builder('c3', CounterMode.INCREMENT)
        c = builder.build()

        @Counter.increase(name='c3', num=2)
        def counter_decorator_test():
            # do nothing
            pass

        for i in range(1, 10):
            counter_decorator_test()
            meterdata = meter_service.transform(c)
            self.assertEqual(meterdata.singleValue.value, c.count)
            self.assertEqual(i * 2, meterdata.singleValue.value)

    def test_counter_timer_decarator(self):
        builder = Counter.Builder('c4', CounterMode.INCREMENT)
        c = builder.build()

        ls = [i / 10 for i in range(10)]

        @Counter.timer(name='c4')
        def counter_decorator_test(s):
            time.sleep(s)

        total = 0
        for _ in range(1, 5):
            random.shuffle(ls)
            for i in ls:
                counter_decorator_test(i)
                total += i
                meterdata = meter_service.transform(c)
                self.assertEqual(meterdata.singleValue.value, c.count)
                self.assertLessEqual(abs(total - meterdata.singleValue.value), tolerance)

    def test_histogram(self):
        builder = Histogram.Builder('h1', list(range(0, 10)))
        h = builder.build()

        for repeat in range(1, 10):
            ls = list(range(1, 10))
            random.shuffle(ls)

            for i in ls:
                h.add_value(i)
                self.assertEqual(repeat, h.find_bucket(i).count)
                meterdata = meter_service.transform(h)
                self.assertEqual(repeat, meterdata.histogram.values[i - 1].count)

    def test_histogram_timer_decarator(self):
        builder = Histogram.Builder('h2', [i / 10 for i in range(10)])
        h = builder.build()

        ls = [i / 10 for i in range(10)]

        @Histogram.timer(name='h2')
        def histogram_decorator_test(s):
            time.sleep(s)

        for repeat in range(1, 5):
            random.shuffle(ls)
            for i in ls:
                histogram_decorator_test(i)
                idx = int(i * 10)
                meterdata = meter_service.transform(h)
                self.assertEqual(repeat, meterdata.histogram.values[idx].count)

    def test_histogram_with_satement(self):
        builder = Histogram.Builder('h3', [i / 10 for i in range(10)])
        h = builder.build()

        ls = [i / 10 for i in range(10)]

        for repeat in range(1, 5):
            random.shuffle(ls)
            for i in ls:
                with h.create_timer():
                    time.sleep(i)
                idx = int(i * 10)
                meterdata = meter_service.transform(h)
                self.assertEqual(repeat, meterdata.histogram.values[idx].count)


    def test_gauge(self):
        ls = list(range(1, 10))
        random.shuffle(ls)
        builder = Gauge.Builder('g1', iter(ls))
        g = builder.build()

        for i in ls:
            meterdata = meter_service.transform(g)
            self.assertEqual(i, meterdata.singleValue.value)


if __name__ == '__main__':
    unittest.main()
