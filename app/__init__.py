import os
from flask import Flask
from app.views import views as views

# flask
app             = Flask(__name__)
app.secret_key  = os.environ['FLASK_APP_SECRET']
app.register_blueprint(views)
