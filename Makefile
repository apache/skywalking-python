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

VERSION ?= next

# determine host platform
ifeq ($(OS),Windows_NT)
    OS := Windows
else ifeq ($(shell uname -s),Darwin)
    OS := Darwin
else
    OS := $(shell sh -c 'uname 2>/dev/null || echo Unknown')
endif

.PHONY: poetry poetry-fallback
# poetry installer may not work on macOS's default python
# falls back to pipx installer
poetry-fallback:
	python3 -m pip install --user pipx
	python3 -m pipx ensurepath
	pipx install poetry
	pipx upgrade poetry

poetry:
ifeq ($(OS),Windows)
	-powershell (Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | py -
	poetry self update
else
	-curl -sSL https://install.python-poetry.org | python3 -
	poetry self update || $(MAKE) poetry-fallback
endif

.PHONY: gen
gen:
	poetry run pip install grpcio-tools packaging
	poetry run python3 tools/grpc_code_gen.py

.PHONY: gen-basic
gen-basic:
	python3 -m pip install grpcio-tools packaging
	python3 tools/grpc_code_gen.py

.PHONY: install
install: gen-basic
	python3 -m pip install --upgrade pip
	python3 -m pip install .[all]

.PHONY: env
env: poetry gen
	poetry install
	poetry run pip install --upgrade pip


.PHONY: lint
# flake8 configurations should go to the file setup.cfg
lint: clean
	poetry run flake8 .

.PHONY: fix
# fix problems described in CodingStyle.md - verify outcome with extra care
fix:
	poetry run unify -r --in-place .
	poetry run flynt -tc -v .

.PHONY: doc-gen
doc-gen: gen
	poetry run python3 tools/plugin_doc_gen.py

.PHONY: check-doc-gen
check-doc-gen: doc-gen
	@if [ ! -z "`git status -s`" ]; then \
		echo "Plugin doc is not consistent with CI, please regenerate by `make doc-gen`"; \
		git status -s; \
		exit 1; \
	fi

.PHONY: license
license: clean
	docker run -it --rm -v $(shell pwd):/github/workspace ghcr.io/apache/skywalking-eyes/license-eye:20da317d1ad158e79e24355fdc28f53370e94c8a header check

.PHONY: test
test: env
	sudo apt-get -y install jq
	docker build --build-arg BASE_PYTHON_IMAGE=3.7 -t apache/skywalking-python-agent:latest-plugin --no-cache . -f tests/plugin/Dockerfile.plugin
	poetry run pytest -v $(bash tests/gather_test_paths.sh)

.PHONY: package
package: clean gen
	poetry build

.PHONY: upload-test
upload-test: package
	poetry run twine upload --repository-url https://test.pypi.org/legacy/ dist/*

.PHONY: upload
upload: package
	poetry run twine upload dist/*

.PHONY: build-image
build-image:
	$(MAKE) -C docker build

.PHONY: push-image
push-image:
	$(MAKE) -C docker push

.PHONY: clean
# FIXME change to python based so we can run on windows
clean:
	rm -rf skywalking/protocol
	rm -rf apache_skywalking.egg-info dist build
	rm -rf skywalking-python*.tgz*
	find . -name "__pycache__" -exec rm -r {} +
	find . -name ".pytest_cache" -exec rm -r {} +
	find . -name "*.pyc" -exec rm -r {} +

.PHONY: release
release: clean lint license
	-tar -zcvf skywalking-python-src-$(VERSION).tgz --exclude .venv *
	gpg --batch --yes --armor --detach-sig skywalking-python-src-$(VERSION).tgz
	shasum -a 512 skywalking-python-src-$(VERSION).tgz > skywalking-python-src-$(VERSION).tgz.sha512
