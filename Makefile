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
	python3 -m pip install grpcio-tools
	python3 -m pip install flake8

gen:
	python3 -m grpc_tools.protoc -I protocol --python_out=. --grpc_python_out=. protocol/**/*.proto

lint: clean
	flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
	flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics

license: clean
	python3 tools/check-license-header.py skywalking tests tools

test: gen
	python3 -m unittest  -v

clean:
	rm -rf browser
	rm -rf common
	rm -rf language_agent
	rm -rf management
	rm -rf profile
	rm -rf service_mesh_probe
	find . -type d -name  "__pycache__" -exec rm -r {} +