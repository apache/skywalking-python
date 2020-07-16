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

Write-Output "Creating virtual environment"

& python -m venv '..\venv'

Write-Output "Virtual env created"

$PYEXE= Join-Path -Path $PSScriptRoot -ChildPath '..\venv\Scripts\python.exe'
& $PYEXE -m pip install --upgrade pip

Write-Output "Pip upgrade complete. Installing packages from requirements.txt"

foreach($package in Get-Content ..\requirements.txt) {
    & $PYEXE -m pip install $package
}
