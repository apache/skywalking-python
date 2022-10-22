
from gevent import monkey
monkey.patch_all()
import gevent.threading
import grpc.experimental.gevent as grpc_gevent     # key point
grpc_gevent.init_gevent()   # key point
from skywalking import config, agent  
config.logging_level = 'DEBUG'
# config.disable_plugins = ['sw_tornado']
agent.start()
from main import app

