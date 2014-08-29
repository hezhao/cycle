from flask import Flask
from flask_sslify import SSLify
from app.views import views as views

# flask
app        = Flask(__name__)
sslify     = SSLify(app, permanent=True)

# blueprints
app.register_blueprint(views)
