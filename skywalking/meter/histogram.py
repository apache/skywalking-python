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

import threading
import timeit
from skywalking.meter.meter import BaseMeter, MeterType
from skywalking.protocol.language_agent.Meter_pb2 import MeterBucketValue, MeterData, MeterHistogram


class Histogram(BaseMeter):
    def __init__(self, name: str, steps, min_value=0, tags=None):
        super().__init__(name, tags)
        self.min_value = min_value

        # check if a list is empty?
        # https://stackoverflow.com/a/53522/9845190
        if not steps:
            raise Exception('steps must not be empty')

        # sort and deduplicate
        # https://stackoverflow.com/a/2931683/9845190
        steps = sorted(set(steps))

        if steps[0] < self.min_value:
            raise Exception('steps are invalid')
        elif steps[0] != self.min_value:
            steps.insert(0, self.min_value)
        self.init_bucks(steps)


    def add_value(self, value):
        bucket = self.find_bucket(value)
        if bucket is None:
            return

        bucket.increment(1)

    def find_bucket(self, value):
        left = 0
        right = len(self.buckets)

        # find the first bucket greater than or equal to the value
        while left < right:
            mid = (left + right) // 2
            if self.buckets[mid].bucket < value:
                left = mid + 1
            else:
                right = mid

        left -= 1

        return self.buckets[left] if left < len(self.buckets) and left >= 0 else None


    def init_bucks(self, steps):
        self.buckets = [Histogram.Bucket(step) for step in steps]

    def transform(self):
        values = [bucket.transform() for bucket in self.buckets]
        return MeterData(histogram=MeterHistogram(name=self.get_name(), labels=self.transform_tags(), values=values))

    def get_type(self):
        return MeterType.HISTOGRAM

    def create_timer(self):
        return Histogram.Timer(self)

    class Bucket():
        def __init__(self, bucket):
            self.bucket = bucket
            self.count = 0
            self._lock = threading.Lock()

        def increment(self, count):
            with self._lock:
                self.count += count

        def transform(self):
            return MeterBucketValue(bucket=self.bucket, count=self.count)

        def __hash__(self) -> int:
            return hash((self.bucket, self.count))

    class Timer():
        def __init__(self, metrics):
            self.metrics = metrics

        def __enter__(self):
            self.start = timeit.default_timer()


        def __exit__(self, exc_type, exc_value, exc_tb):
            self.stop = timeit.default_timer()
            duration = self.stop - self.start
            self.metrics.add_value(duration)

    @staticmethod
    def timer(name: str):
        def inner(func):
            def wrapper(*args, **kwargs):
                start = timeit.default_timer()
                func(*args, **kwargs)
                stop = timeit.default_timer()
                duration = stop - start
                histogram = Histogram.meter_service.get_meter(name)
                histogram.add_value(duration)

            return wrapper

        return inner

    class Builder(BaseMeter.Builder):
        def __init__(self, name: str, steps, min_value=0, tags=None):
            self.meter = Histogram(name, steps, min_value, tags)
