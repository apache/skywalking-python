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


class ServiceManagementClient(object):
    def send_instance_props(self):
        raise NotImplementedError()

    def send_heart_beat(self):
        raise NotImplementedError()


class TraceSegmentReportService(object):
    def report(self, generator):
        raise NotImplementedError()


class MeterReportService(object):
    def report(self, generator):
        raise NotImplementedError()


class LogDataReportService(object):
    def report(self, generator):
        raise NotImplementedError()


class ProfileTaskChannelService(object):
    def do_query(self):
        raise NotImplementedError()

    def send(self, generator):
        raise NotImplementedError()
