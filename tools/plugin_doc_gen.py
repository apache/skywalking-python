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

"""
A tool to generate test matrix report for SkyWalking Python Plugins
"""
import pkgutil

from skywalking.plugins import __path__ as plugins_path

table_head = """
Library | Python Version: Lib Version | Plugin Name
| :--- | :--- | :--- |
"""


def generate_doc_table():
    """
    Generates a test matrix table to the current dir
    # TODO inject into the plugins.md doc instead of manual copy

    Returns: None

    """
    table_entries = []
    for importer, modname, ispkg in pkgutil.iter_modules(plugins_path):
        plugin = importer.find_module(modname).load_module(modname)

        plugin_support_matrix = plugin.support_matrix
        plugin_support_links = plugin.link_vector
        libs_tested = list(plugin_support_matrix.keys())
        links_tested = plugin_support_links

        for lib, link in zip(libs_tested, links_tested):  # NOTE: maybe a two lib support like http.server + werkzeug
            lib_entry = str(lib)
            lib_link = link
            version_vector = plugin_support_matrix[lib_entry]  # type: dict
            pretty_vector = ""
            for python_version in version_vector:  # e.g. {'>=3.10': ['2.5', '2.6'], '>=3.6': ['2.4.1', '2.5', '2.6']}
                lib_versions = version_vector[python_version]
                pretty_vector += f"Python {python_version} " \
                                 f"- {str(lib_versions) if lib_versions else 'NOT SUPPORTED YET'}; "
            table_entry = f"| [{lib_entry}]({lib_link}) | {pretty_vector} | `{modname}` |"
            table_entries.append(table_entry)

    with open("plugin_doc.md", "w") as doc:
        doc.write(table_head)
        for entry in table_entries:
            doc.write(entry + '\n')


if __name__ == "__main__":
    generate_doc_table()
