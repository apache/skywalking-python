# from gevent import monkey
# monkey.patch_all()
# import grpc.experimental.gevent as grpc_gevent     # key point
# grpc_gevent.init_gevent()   # key point
# from skywalking import config, agent  
# config.logging_level = 'DEBUG'
# config.init()
# agent.start()

import time
import random
from flask import Flask, request

app = Flask(__name__)
   
@app.route('/artist', methods=['POST'])
def artist():
    try:

        time.sleep(random.random())
        payload = request.get_json()
        print(f" args:{payload}")
        return {"artist": "song"}
        
    except Exception as e:  # noqa
        print(f"error: {e}")
        return {'message': e}


if __name__ == '__main__':
    # noinspection PyTypeChecker
    app.run(host='0.0.0.0', port=9090)