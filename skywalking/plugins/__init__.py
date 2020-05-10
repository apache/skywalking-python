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
import inspect
import logging
import pkgutil
import re

from skywalking import config

import skywalking

logger = logging.getLogger(__name__)


def install():
    for importer, modname, ispkg in pkgutil.iter_modules(skywalking.plugins.__path__):
        disable_patterns = config.disable_plugins
        if isinstance(disable_patterns, str):
            disable_patterns = [re.compile(p.strip()) for p in disable_patterns.split(',') if p.strip()]
        else:
            disable_patterns = [re.compile(p.strip()) for p in disable_patterns if p.strip()]
        if any(pattern.match(modname) for pattern in disable_patterns):
            logger.info('plugin %s is disabled and thus won\'t be installed', modname)
            continue
        logger.debug('installing plugin %s', modname)
        plugin = importer.find_module(modname).load_module(modname)
        if not hasattr(plugin, 'install') or inspect.ismethod(getattr(plugin, 'install')):
            logger.warning('no `install` method in plugin %s, thus the plugin won\'t be installed', modname)
            continue
        plugin.install()
