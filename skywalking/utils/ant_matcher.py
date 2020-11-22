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


import re

reesc = re.compile(r'([.*+?^=!:${}()|\[\]\\])')
recache = {}


def fast_path_match(pattern: str, path: str):
    repat = recache.get(pattern)

    if repat is None:
        repat = recache[pattern] = \
            re.compile('^(?:' +                       # this could handle multiple patterns in one by joining with '|'
                       '(?:(?:[^/]+/)*[^/]+)?'.join(  # replaces "**"
                           '[^/]*'.join(              # replaces "*"
                               '[^/]'.join(           # replaces "?"
                                   reesc.sub(r'\\\1', s) for s in p2.split('?')
                               ) for p2 in p1.split('*')
                           ) for p1 in pattern.split('**')
                       ) + ')$')

    return bool(repat.match(path))
