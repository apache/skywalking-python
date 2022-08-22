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

import timeit
from skywalking.meter.meter import BaseMeter, MeterType
from skywalking.protocol.language_agent.Meter_pb2 import MeterBucketValue, MeterData, MeterHistogram, MeterSingleValue


class Histogram(BaseMeter):
    def __init__(self, name: str, steps, minValue=0, tags=[]):
        super().__init__(name, tags)
        self.minValue = minValue

        # https://stackoverflow.com/a/53522/9845190
        if not steps:
            # raise error
            pass

        # https://stackoverflow.com/a/2931683/9845190
        steps = sorted(set(steps))

        if steps[0] < self.minValue:
            # raise error
            pass
        elif steps[0] != self.minValue:
            steps.insert(0, self.minValue)
        self.initBucks(steps)


    def addValue(self, value):
        bucket = self.findBucket(value)
        if bucket == None:
            return 
        
        bucket.increment(1)

    def findBucket(self, value):
        l = 0
        r = len(self.buckets)
        
        # find the first bucket greater than or equal the value
        while(l < r):
            mid = (l + r) // 2
            if(self.buckets[mid].bucket < value):
                l = mid + 1
            else:
                r = mid
        
        l -= 1

        return self.buckets[l] if l < len(self.buckets) and l >= 0 else None


    def initBucks(self, steps):
        self.buckets = [Histogram.Bucket(step) for step in steps]

    def transform(self):
        values = [bucket.transform() for bucket in self.buckets]
        return MeterData(histogram=MeterHistogram(name=self.getName(), labels=self.transformTags(), values=values))
    
    def getType(self):
        return MeterType.HISTOGRAM

    def createTimer(self):
        return Histogram.Timer(self)

    class Bucket():
        
        def __init__(self, bucket):
            self.bucket = bucket
            self.count = 0
        
        def increment(self, count):
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
            self.metrics.addValue(duration)
    
    @staticmethod
    def timer(name: str):
        def Inner(func):
            def wrapper(*args, **kwargs):
                start = timeit.default_timer()
                func(*args, **kwargs)
                stop = timeit.default_timer()
                duration = stop - start
                histogram = Histogram.meter_service.getMeterByName(name)
                histogram.addValue(duration)

            return wrapper
            
        return Inner

    @staticmethod
    def addValtu(name: str, num):
        def Inner(func):
            def wrapper(*args, **kwargs):
                func(*args, **kwargs)
                histogram = Histogram.meter_service.getMeterByName(name)
                histogram.addValue(num)

            return wrapper
            
        return Inner

