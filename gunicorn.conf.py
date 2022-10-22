#################################################
# Gunicorn config for Flask
#################################################

from gevent import monkey
monkey.patch_all()

bind = '0.0.0.0:5000'

# configure number of gunicorn workers
# import multiprocessing
workers = 1

worker_class = 'gevent'

# dont daemonize; running inside docker
daemon = False
timeout = 60
keepalive = 70
pidfile = '/tmp/gunicorn.pid'
limit_request_line = 8194

# error log to STDERR
errorlog = '-'
loglevel = 'info'

# access logs to STDERR also
accesslog = '-'
access_log_format = '%(h)s %(u)s [%(t)s] "%(m)s %(U)s %(H)s" %(s)s %(B)s %(T)s "%(f)s" "%(a)s" test-gevent-service'
