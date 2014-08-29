import os
from app import app

app.secret_key  = os.environ['FLASK_APP_SECRET']