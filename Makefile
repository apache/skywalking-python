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

VERSION ?= latest

# determine host platform
VENV_DIR = venv
VENV = $(VENV_DIR)/bin
ifeq (win32,$(shell python3 -c "import sys; print(sys.platform)"))
VENV=$(VENV_DIR)/Scripts
endif

.PHONY: license

setup:
	python3 -m pip install --upgrade pip
	python3 -m pip install grpcio --ignore-installed

setup-test: setup
	pip3 install -e .[test]

gen:
	python3 -m grpc_tools.protoc --version || python3 -m pip install grpcio-tools
	python3 tools/codegen.py

# flake8 configurations should go to the file setup.cfg
lint: clean
	python3 -m pip install -r requirements-style.txt
	flake8 .

# used in development
dev-setup:
	$(VENV)/python -m pip install -r requirements-style.txt

dev-check: dev-setup
	$(VENV)/flake8 .

# fix problems described in CodingStyle.md - verify outcome with extra care
dev-fix: dev-setup
	$(VENV)/isort .
	$(VENV)/unify -r --in-place .
	$(VENV)/flynt -tc -v .

doc-gen:
	$(VENV)/python tools/doc/plugin_doc_gen.py

license: clean
	python3 tools/check-license-header.py skywalking tests tools

test: gen setup-test
	python3 -m pytest -v tests

# This is intended for GitHub CI only
test-parallel-setup: gen setup-test

install: gen
	python3 setup.py install --force

package: clean gen
	python3 setup.py sdist bdist_wheel

upload-test: package
	twine upload --repository-url https://test.pypi.org/legacy/ dist/*

upload: package
	twine upload dist/*

build-image:
	$(MAKE) -C docker build

push-image:
	$(MAKE) -C docker push

clean:
	rm -rf skywalking/protocol
	rm -rf apache_skywalking.egg-info dist build
	rm -rf skywalking-python*.tgz*
	find . -name "__pycache__" -exec rm -r {} +
	find . -name ".pytest_cache" -exec rm -r {} +
	find . -name "*.pyc" -exec rm -r {} +

release: clean lint license
	-tar -zcvf skywalking-python-src-$(VERSION).tgz *
	gpg --batch --yes --armor --detach-sig skywalking-python-src-$(VERSION).tgz
	shasum -a 512 skywalking-python-src-$(VERSION).tgz > skywalking-python-src-$(VERSION).tgz.sha512
