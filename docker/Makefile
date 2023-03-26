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

HUB ?= docker.io/apache
PROJECT ?= skywalking-python

D := docker

P := grpc http kafka

TARGETS := py3.7 py3.8 py3.9 py3.10 py3.7-slim py3.8-slim py3.9-slim py3.10-slim

py3.7: BASE_PYTHON_IMAGE = python:3.7
py3.8: BASE_PYTHON_IMAGE = python:3.8
py3.9: BASE_PYTHON_IMAGE = python:3.9
py3.10: BASE_PYTHON_IMAGE = python:3.10
py3.11: BASE_PYTHON_IMAGE = python:3.11
py3.7-slim: BASE_PYTHON_IMAGE = python:3.7-slim
py3.8-slim: BASE_PYTHON_IMAGE = python:3.8-slim
py3.9-slim: BASE_PYTHON_IMAGE = python:3.9-slim
py3.10-slim: BASE_PYTHON_IMAGE = python:3.10-slim
py3.11-slim: BASE_PYTHON_IMAGE = python:3.11-slim

push-py3.7: BASE_PYTHON_IMAGE = python:3.7
push-py3.8: BASE_PYTHON_IMAGE = python:3.8
push-py3.9: BASE_PYTHON_IMAGE = python:3.9
push-py3.10: BASE_PYTHON_IMAGE = python:3.10
push-py3.11: BASE_PYTHON_IMAGE = python:3.11
push-py3.7-slim: BASE_PYTHON_IMAGE = python:3.7-slim
push-py3.8-slim: BASE_PYTHON_IMAGE = python:3.8-slim
push-py3.9-slim: BASE_PYTHON_IMAGE = python:3.9-slim
push-py3.10-slim: BASE_PYTHON_IMAGE = python:3.10-slim
push-py3.11-slim: BASE_PYTHON_IMAGE = python:3.11-slim

push-py3.7: BUILDER_PYTHON_IMAGE = python:3.7
push-py3.8: BUILDER_PYTHON_IMAGE = python:3.8
push-py3.9: BUILDER_PYTHON_IMAGE = python:3.9
push-py3.10: BUILDER_PYTHON_IMAGE = python:3.10
push-py3.11: BUILDER_PYTHON_IMAGE = python:3.11
push-py3.7-slim: BUILDER_PYTHON_IMAGE = python:3.7
push-py3.8-slim: BUILDER_PYTHON_IMAGE = python:3.8
push-py3.9-slim: BUILDER_PYTHON_IMAGE = python:3.9
push-py3.10-slim: BUILDER_PYTHON_IMAGE = python:3.10
push-py3.11-slim: BUILDER_PYTHON_IMAGE = python:3.11

PUSH_TARGETS := $(TARGETS:%=push-%)

build: $(TARGETS)
push: $(PUSH_TARGETS)



$(TARGETS):
	cd ..; \
	for p in $(P); do \
		$(D) build $(SW_BUILD_ARGS) \
				-f docker/Dockerfile \
				--build-arg BASE_PYTHON_IMAGE=$(BASE_PYTHON_IMAGE) \
				--build-arg SW_PYTHON_AGENT_PROTOCOL=$$p \
				--build-arg SW_PYTHON_AGENT_VERSION=${AGENT_VERSION} \
				-t $(HUB)/$(PROJECT):${AGENT_VERSION}-$$p-$@ \
				. ; \
	done


$(PUSH_TARGETS):
	$(eval version := $(subst push-,,$@))
	docker buildx create --driver docker-container --name skywalking_python_main_$(version) > /dev/null 2>&1 || true;
	cd ..; \
	for p in $(P); do \
		$(D) buildx build $(SW_BUILD_ARGS) \
				--builder skywalking_python_main_$(version) \
				-f docker/Dockerfile \
				--platform linux/amd64,linux/arm64 --push \
				--build-arg BASE_PYTHON_IMAGE=$(BASE_PYTHON_IMAGE) \
				--build-arg BUILDER_PYTHON_IMAGE=$(BUILDER_PYTHON_IMAGE) \
				--build-arg SW_PYTHON_AGENT_PROTOCOL=$$p \
				--build-arg SW_PYTHON_AGENT_VERSION=${AGENT_VERSION} \
				-t $(HUB)/$(PROJECT):${AGENT_VERSION}-$$p-${version} \
				. ; \
	done
	docker buildx rm skywalking_python_main_$(version) || true;
