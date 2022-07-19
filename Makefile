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

$(VENV):
	python3 -m venv $(VENV_DIR)
	$(VENV)/python -m pip install --upgrade pip
	$(VENV)/python -m pip install wheel twine

setup: $(VENV)
	$(VENV)/python -m pip install grpcio --ignore-installed

setup-test: setup gen
	$(VENV)/pip install -e .[test]

gen: $(VENV)
	$(VENV)/python -m grpc_tools.protoc --version || $(VENV)/python -m pip install grpcio-tools
	$(VENV)/python tools/codegen.py

# flake8 configurations should go to the file setup.cfg
lint: clean $(VENV)
	$(VENV)/python -m pip install -r requirements-style.txt
	$(VENV)/flake8 .

# used in development
dev-setup: $(VENV)
	$(VENV)/python -m pip install -r requirements-style.txt

dev-check: dev-setup
	$(VENV)/flake8 .

# fix problems described in CodingStyle.md - verify outcome with extra care
dev-fix: dev-setup
	$(VENV)/isort .
	$(VENV)/unify -r --in-place .
	$(VENV)/flynt -tc -v .

doc-gen: $(VENV) install
	$(VENV)/python tools/doc/plugin_doc_gen.py

check-doc-gen: dev-setup doc-gen
	@if [ ! -z "`git status -s`" ]; then \
		echo "Plugin doc is not consisitent with CI:"; \
		git status -s; \
		exit 1; \
	fi

license: clean
	docker run -it --rm -v $(shell pwd):/github/workspace ghcr.io/apache/skywalking-eyes/license-eye:f461a46e74e5fa22e9f9599a355ab4f0ac265469 header check

test: gen setup-test
	$(VENV)/python -m pytest -v tests

# This is intended for GitHub CI only
test-parallel-setup: gen setup-test

install: gen
	$(VENV)/python setup.py install --force

package: clean gen
	$(VENV)/python setup.py sdist bdist_wheel

upload-test: package
	$(VENV)/twine upload --repository-url https://test.pypi.org/legacy/ dist/*

upload: package
	$(VENV)/twine upload dist/*

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
	-tar -zcvf skywalking-python-src-$(VERSION).tgz --exclude venv *
	gpg --batch --yes --armor --detach-sig skywalking-python-src-$(VERSION).tgz
	shasum -a 512 skywalking-python-src-$(VERSION).tgz > skywalking-python-src-$(VERSION).tgz.sha512
