# from flask import Flask
#
# from skywalking import config, agent
#
# config.service_name = 'consumer'
# config.logging_level = 'DEBUG'
# agent.start()
#
# app = Flask(__name__)
#
# @app.route('/')
# def index():
#     return "<span style='color:red'>I am app 1</span>"
#
#
# # app.run()
# if __name__ == "__main__":
#     app.run(host='0.0.0.0')
