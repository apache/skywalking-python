import requests
from flask import Flask
app = Flask(__name__)

@app.route('/')
def hello_world():
    return 'Hello World!'

    
def output():
    return "boooo"

def foo():
    req = requests.get("http://127.0.0.1:5000/")
    return req.text
@app.route('/hello')
def hello():
    foo()
    return 'Hello !'+ foo()

print(app.url_map)
if __name__ == '__main__':
    app.run()