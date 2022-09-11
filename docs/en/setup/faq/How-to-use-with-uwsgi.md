# How to use with uWSGI ?

[uWSGI](https://uwsgi-docs.readthedocs.io/en/latest/) is popular in the Python ecosystem. It is a lightweight, fast, and easy-to-use web server.

When uWSGI is used with Skywalking, the pre-fork mechanism of uWSGI must be considered. Some discussion can be found here .
* [[Python] Apache Skywalking, flask uwsgi, no metrics send to server · Issue #6324 · apache/skywalking](https://github.com/apache/skywalking/issues/6324)
* [[Bug] skywalking-python not work with uwsgi + flask in master workers mode and threads mode · Issue #8566 · apache/skywalking](https://github.com/apache/skywalking/issues/8566)

If you get some problems when using skywalking, you can try to use the following method to call [`@postfork`](https://uwsgi-docs.readthedocs.io/en/latest/PythonDecorators.html#uwsgidecorators.postfork), the low-level api of uWSGI to initialize the skywalking client.

The following is an example of the use of uWSGI and flask, the initialization parameters of skywalking can be referred to [Legacy Setup](https://skywalking.apache.org/docs/skywalking-python/next/en/setup/intrusive/#legacy-setup)

```python
# main.py
from uwsgidecorators import postfork
from skywalking import agent, config

@postfork
def init_tracing():
    config.init(collector_address='127.0.0.1:11800', service_name='your awesome service')

    agent.start()

from flask import Flask
app = Flask(__name__)

@app.route('/')
def hello_world():
    return 'Hello World!'

if __name__ == '__main__':
    app.run()
```

```shell
uwsgi --die-on-term \
    --http 0.0.0.0:5000 \
    --http-manage-expect \
    --master --workers 3 \
    --enable-threads \
    --threads 3 \
    --manage-script-name \
    --mount /=main:app
```