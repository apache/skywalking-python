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

FROM openjdk:8

WORKDIR /tests

ARG COMMIT_HASH=3c9d7099f05dc4a4b937c8a47506e56c130b6221

ADD https://github.com/apache/skywalking-agent-test-tool/archive/${COMMIT_HASH}.tar.gz .

RUN tar -xf ${COMMIT_HASH}.tar.gz --strip 1

RUN rm ${COMMIT_HASH}.tar.gz

RUN ./mvnw -B -DskipTests package

FROM openjdk:8

EXPOSE 19876 12800

WORKDIR /tests

COPY --from=0 /tests/dist/skywalking-mock-collector.tar.gz /tests

RUN tar -xf skywalking-mock-collector.tar.gz --strip 1

RUN chmod +x bin/collector-startup.sh

ENTRYPOINT bin/collector-startup.sh
