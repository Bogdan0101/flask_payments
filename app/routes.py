from flask import Flask
from asgiref.wsgi import WsgiToAsgi

app_flask = Flask(__name__)


@app_flask.route("/")
async def index():
    return "Hello World!"


app = WsgiToAsgi(app_flask)
