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

class Tag:
    overridable = True

    def __init__(self, val):
        self.val = val


class TagHttpMethod(Tag):
    key = 'http.method'


class TagHttpURL(Tag):
    key = 'http.url'


class TagHttpStatusCode(Tag):
    key = 'http.status.code'


class TagHttpStatusMsg(Tag):
    key = 'http.status.msg'


class TagHttpParams(Tag):
    key = 'http.params'


class TagDbType(Tag):
    key = 'db.type'


class TagDbInstance(Tag):
    key = 'db.instance'


class TagDbStatement(Tag):
    key = 'db.statement'


class TagDbSqlParameters(Tag):
    key = 'db.sql.parameters'
    overridable = False


class TagMqBroker(Tag):
    key = 'mq.broker'


class TagMqTopic(Tag):
    key = 'mq.topic'


class TagMqQueue(Tag):
    key = 'mq.queue'


class TagCeleryParameters(Tag):
    key = 'celery.parameters'
