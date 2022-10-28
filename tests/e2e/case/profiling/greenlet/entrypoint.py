from gevent import monkey
monkey.patch_all()
import grpc.experimental.gevent as grpc_gevent     # key point
grpc_gevent.init_gevent()   # key point
from skywalking import config, agent  
config.logging_level = 'DEBUG'
config.init()
agent.start()

from provider import app