set -ex
pip install gunicorn gevent
gunicorn -k gevent -b :9090 --chdir /services entrypoint:app