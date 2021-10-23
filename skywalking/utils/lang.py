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

import base64


def tostring(cls):
    def __str__(self): # noqa
        return f"{type(self).__name__}@{id(self)}[{', '.join(f'{k}={str(v)}' for (k, v) in vars(self).items())}]"
    cls.__str__ = __str__
    return cls


def b64encode(s: str = '') -> str:
    return base64.b64encode(s.encode('utf8')).decode('utf8')


def b64decode(s: str = '') -> str:
    return base64.b64decode(s).decode('utf8')
