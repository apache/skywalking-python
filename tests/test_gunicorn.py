# -*- coding:utf-8 -*-
# author：huawei
import requests

from skywalking import config, agent


config.service_name = 'consumer'
config.logging_level = 'DEBUG'
config.flask_collect_http_params = True
agent.start()

from flask import Flask, jsonify

app = Flask(__name__)


@app.route("/users", methods=["POST", "GET"])
def application():
    requests.post("http://github.com")

    return jsonify({"test": "hello world"})

# PORT = 9090
# app.run(host='0.0.0.0', port=PORT, debug=True)
