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

from time import sleep

from skywalking import agent, Component, Layer
from skywalking.decorators import trace
from skywalking.trace.context import SpanContext, get_context

if __name__ == '__main__':
    agent.start()
    sleep(3)

    @trace()
    def some_other_method():
        sleep(1)

    @trace()
    def some_method():
        some_other_method()

    for _ in range(1, 20):
        context = get_context()  # type: SpanContext
        with context.new_entry_span(op='https://github.com/1') as s1:
            s1.component = Component.General
            some_method()
            print(s1)
            with context.new_entry_span(op='https://github.com/2') as s2:
                s2.component = Component.General
                s2.layer = Layer.Http
                print(s2)
                sleep(0.5)
                with context.new_exit_span(op='https://github.com/3', peer='127.0.0.1:80') as s3:
                    s3.component = Component.General
                    s3.layer = Layer.Http
                    print(s3)
                    sleep(0.5)
                    with context.new_entry_span(op='https://github.com/4') as s4:
                        s4.component = Component.General
                        s4.layer = Layer.Http
                        print(s4)
                        sleep(0.5)
                with context.new_exit_span(op='https://github.com/5', peer='127.0.0.1:80') as s5:
                    s5.component = Component.General
                    s5.layer = Layer.Http
                    print(s5)
                    sleep(0.5)
        sleep(0.5)
        print()
