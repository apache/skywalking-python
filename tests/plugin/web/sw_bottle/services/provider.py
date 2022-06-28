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

import time
from bottle import route, run


@route('/users', method='POST')
def hello():
    from skywalking.trace.context import get_context
    time.sleep(0.5)
    cor = get_context().get_correlation('correlation')
    cor = cor if cor else 'null'
    data = f"{{'correlation': {cor}}}"
    return data


run(host='localhost', port=9091, debug=True)
