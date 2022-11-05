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
import random
from flask import Flask, request

app = Flask(__name__)


@app.route('/artist', methods=['POST'])
def artist():
    try:

        time.sleep(random.random())
        payload = request.get_json()
        print(f'args: {payload}')

        return {'artist': 'song'}
    except Exception as e:  # noqa
        return {'message': str(e)}


if __name__ == '__main__':
    # noinspection PyTypeChecker
    app.run(host='0.0.0.0', port=9090)
