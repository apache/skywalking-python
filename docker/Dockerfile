# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

ARG BASE_PYTHON_IMAGE
ARG BUILDER_PYTHON_IMAGE
FROM ${BASE_PYTHON_IMAGE} AS base

FROM ${BUILDER_PYTHON_IMAGE} AS builder
RUN pip install --upgrade pip
RUN pip install poetry
COPY ./ /tmp/
RUN make -C /tmp package
RUN pip wheel psutil -w /tmp/dist/

FROM base AS final
COPY --from=builder /tmp/dist/*.whl /tmp/
RUN pip install --upgrade pip
RUN pip install /tmp/psutil*.whl /tmp/apache_skywalking*.whl
RUN rm /tmp/apache_skywalking*.whl /tmp/psutil*.whl
# So that the agent can be auto-started when container is started
ENTRYPOINT ["sw-python"]
