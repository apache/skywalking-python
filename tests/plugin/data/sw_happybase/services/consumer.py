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

import happybase


if __name__ == '__main__':
    from flask import Flask, jsonify

    app = Flask(__name__)
    connection = happybase.Connection('hbase', port=9090)
    connection.open()
    row = b'row_key'
    info = {b'INFO:data': b'value'}
    table_name = 'test'

    def create_table():
        families = {'INFO': {}}
        connection.create_table(table_name, families)

    def save_table():
        table = connection.table(table_name)
        table.put(row, info)

    def get_row():
        table = connection.table(table_name)
        table.row(row)

    @app.route('/users', methods=['POST', 'GET'])
    def application():
        create_table()
        save_table()
        get_row()
        return jsonify({'INFO:data': 'value'})

    PORT = 9090
    app.run(host='0.0.0.0', port=PORT, debug=True)
