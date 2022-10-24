import time
import requests
from flask import Flask

app = Flask(__name__)


@app.route("/")
def hello_world():
    return "Hello World!"


@app.route("/world")
def world():
    return "World!"


def output():
    return "boooo"


def foo():
    req = requests.get("https://www.baidu.com")
    return req.text


@app.route("/hello")
def hello():
    foo()
    return "Hello !" + foo()


def call_sleep():
    output()
    time.sleep(1)


def call_hello():
    call_sleep()
    req = requests.get("http://127.0.0.1:5000/hello")
    return req.text


@app.route("/twice")
def twice():
    current_time = time.time()
    call_sleep()
    print(foo())
    call_sleep()
    return str(time.time() - current_time)


print(app.url_map)
if __name__ == "__main__":
    app.run()
