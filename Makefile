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

.PHONY: license

setup:
	python3 -m pip install --upgrade pip
	python3 -m pip install grpcio --ignore-installed

gen:
	python3 -m grpc_tools.protoc --version || python3 -m pip install grpcio-tools
	python3 -m grpc_tools.protoc -I protocol --python_out=. --grpc_python_out=. protocol/**/*.proto
	touch browser/__init__.py
	touch common/__init__.py
	touch language_agent/__init__.py
	touch management/__init__.py
	touch profile/__init__.py
	touch service_mesh_probe/__init__.py

lint: clean
	flake8 --version || python3 -m pip install flake8
	flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
	flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics

license: clean
	python3 tools/check-license-header.py skywalking tests tools

test: gen
	pip3 install -e .[test]
	python3 -m unittest  -v

install: gen
	python3 setup.py install --force

package: clean gen
	python3 setup.py sdist bdist_wheel

clean:
	rm -rf browser common language_agent management profile service_mesh_probe
	rm -rf skywalking_python.egg-info dist build
	find . -type d -name  "__pycache__" -exec rm -r {} +