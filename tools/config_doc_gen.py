# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

"""
A simple doc generator for configuration options
"""
from skywalking import config

DOC_HEAD = """# Supported Agent Configuration Options

Below is the full list of supported configurations you can set to
customize the agent behavior, please take some time to read the descriptions for what they can achieve.

> Usage: (Pass in intrusive setup)
```
from skywalking import config, agent
config.init(YourConfiguration=YourValue))
agent.start()
```
> Usage: (Pass by environment variables)
```
export SW_AGENT_YourConfiguration=YourValue
```

"""
TABLE_HEAD = """### {}
| Configuration | Environment Variable | Type | Default Value | Description |
| :------------ | :------------ | :------------ | :------------ | :------------ |
"""

OPTIONS = config.options_with_default_value_and_type


def comments_from_file(file_path):
    """
    Get comments from config.py
    """
    comments = []
    analyze = False
    comment_block_begin = False
    with open(file_path, 'r') as config_file:
        lines = config_file.readlines()
        lines = [line.rstrip() for line in lines]
        for line in lines:
            if line.startswith('# THIS MUST PRECEDE DIRECTLY BEFORE LIST OF CONFIG OPTIONS!'):
                analyze = True
                continue
            if line.startswith('# THIS MUST FOLLOW DIRECTLY AFTER LIST OF CONFIG OPTIONS!'):
                break
            if analyze and line.startswith('#'):
                if line.startswith('# BEGIN'):
                    comments.append(line)
                    comment_block_begin = False
                    continue
                if comment_block_begin:
                    comments[-1] += line.lstrip('#') if not comments[-1].endswith('/') else line.lstrip('# ')
                    continue
                comment_block_begin = True
                comments.append(line.lstrip('# '))
            else:  # not comment
                if comment_block_begin:
                    comment_block_begin = False
        return comments


def create_entry(comment: str, config_index: int) -> str:
    """
    Each configuration entry is matched with comment (blocks) by index
    Args:
        comment: comment block
        config_index: index of comment block in the list of comments
    Returns: markdown table entry
    """

    def env_var_name(config_entry):
        return 'SW_' + config_entry.upper()

    configuration = list(OPTIONS.keys())[config_index]
    type_ = OPTIONS[configuration][1]
    default_val = OPTIONS[configuration][0]

    # special case for randomly generated default value
    if configuration == 'agent_instance_name':
        default_val = "str(uuid.uuid1()).replace('-', '')"
    return f'| {configuration} | {env_var_name(configuration)} | {str(type_)} | {default_val} | {comment} |'


def generate_markdown_table() -> None:
    """
    Goes through each configuration entry and its comment block and generates markdown tables
    """
    comments = comments_from_file('skywalking/config.py')

    with open('docs/en/setup/Configuration.md', 'w') as plugin_doc:
        plugin_doc.write(DOC_HEAD)
        offset = 0
        for config_index, comment in enumerate(comments):
            if comment.startswith('# BEGIN'):
                # remove `#BEGIN: `
                plugin_doc.write(TABLE_HEAD.format(comment[8:]))
                offset += 1
            else:
                table_entry = create_entry(comment, config_index - offset)
                plugin_doc.write(f'{table_entry}\n')


def config_env_var_verify():
    """
    A naive checker to verify if all configuration entries have corresponding environment
    (prevents common typo but not all)
    """
    with open('skywalking/config.py', 'r') as config_file:
        data = config_file.read().replace('\n', '')
        for each in OPTIONS.keys():
            if f'_{each.upper()}' not in data:
                raise Exception(f'Environment variable for {each.upper()} is not found in config.py\n'
                                f'This means you have a mismatch of config.py variable and env var name')


if __name__ == '__main__':
    generate_markdown_table()
    config_env_var_verify()
