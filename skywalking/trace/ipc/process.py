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

from multiprocessing import Process

from skywalking import config, agent


class SwProcess(Process):

    def __init__(self, group=None, target=None, name=None, args=(), kwargs={}, *,
                 daemon=None):
        super(SwProcess, self).__init__(group=group, target=target, name=name, args=args, kwargs=kwargs, daemon=daemon)
        self._sw_config = config.serialize()

    def run(self):
        if agent.started() is False:
            config.deserialize(self._sw_config)
            agent.start()
        super(SwProcess, self).run()
