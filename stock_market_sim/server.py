from flask import Flask
from flask_restx import Api
from namespaces.host import api as host_ns
from namespaces.client import api as client_ns

app = Flask(__name__)
api = Api(app)

api.add_namespace(host_ns, path='/host')
api.add_namespace(client_ns, path='/client')

if __name__ == '__main__':
    app.run(debug=True, threaded=True)