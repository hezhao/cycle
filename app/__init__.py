import os
from flask import Flask
from app.views import views as views
from flask_sslify import SSLify

# flask
app             = Flask(__name__)
app.secret_key  = os.environ['FLASK_APP_SECRET']
app.register_blueprint(views)
sslify          = SSLify(app, permanent=True)
