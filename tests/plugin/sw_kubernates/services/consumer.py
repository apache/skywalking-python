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


from skywalking import agent, config

if __name__ == '__main__':
    config.service_name = 'consumer'
    config.logging_level = 'DEBUG'
    agent.start()

    from flask import Flask, jsonify
    from kubernetes import client

    app = Flask(__name__)

    k8s_server = ""
    k8s_token = ""

    configuration = client.Configuration()
    configuration.host = k8s_server
    configuration.verify_ssl = False
    configuration.api_key = {"authorization": "Bearer " + k8s_token}
    connection = client.api_client.ApiClient(configuration=configuration)
    core_conn = client.CoreV1Api(connection)
    apps_conn = client.AppsV1Api(connection)
    net_conn = client.NetworkingV1beta1Api(connection)


    @app.route("/users", methods=["POST", "GET"])
    def application():
        core_conn.list_namespace()
        core_conn.list_pod_for_all_namespaces()
        apps_conn.list_deployment_for_all_namespaces()
        net_conn.list_ingress_for_all_namespaces()
        return jsonify({"song": "Despacito", "artist": "Luis Fonsi"})


    PORT = 9090
    app.run(host='0.0.0.0', port=PORT, debug=True)
