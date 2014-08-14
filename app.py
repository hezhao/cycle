import os
from store import Store
from datetime import datetime, timedelta
from flask import Flask, url_for, request, session, redirect
from moves import MovesClient


app = Flask(__name__)

# config vars
client_id       = os.environ['CLIENT_ID']
client_secret   = os.environ['CLIENT_SECRET']
redis_url       = os.environ['REDISTOGO_URL']

# class instances
moves           = MovesClient(client_id, client_secret)
store           = Store(redis_url)

@app.route("/")
def index():
    if 'access_token' not in session:
        oauth_return_url = url_for('oauth_return', _external=True)
        auth_url = moves.build_oauth_url(oauth_return_url)
        return 'Authorize this application: <a href="%s">%s</a>' % \
            (auth_url, auth_url)
    return redirect(url_for('show_info'))

@app.route("/myinfo")
def myinfo():
    profile = moves.user_profile(access_token=access_token)
    response = 'User ID: %s<br />First day using Moves: %s' % \
        (profile['userId'], profile['profile']['firstDate'])
    return response + "<br /><a href=\"%s\">Info for today</a>" % url_for('today') + \
        "<br /><a href=\"%s\">Logout</a>" % url_for('logout')


@app.route("/oauth_return")
def oauth_return():
    error = request.values.get('error', None)
    if error is not None:
        return error
    oauth_return_url = url_for('oauth_return', _external=True)
    code = request.args.get("code")
    response = moves.get_oauth_token(code, redirect_uri=oauth_return_url)
    
    # store access_token and user_id in session
    session['access_token'] = response['access_token']
    session['user_id'] = response['user_id']

    # user:[user_id] = access_token
    store.set_access_token(session['user_id'], response['access_token'])

    # user:[user_id] = refresh_token
    store.set_refresh_token(session['user_id'], response['refresh_token'])

    return redirect(url_for('show_info'))


@app.route('/logout')
def logout():
    if 'access_token' in session:
        del(session['access_token'])
    return redirect(url_for('index'))


@app.route("/info")
def show_info():
    profile = moves.user_profile(access_token=session['access_token'])
    response = 'User ID: %s<br />First day using Moves: %s' % \
        (profile['userId'], profile['profile']['firstDate'])
    return response + "<br /><a href=\"%s\">Info for today</a>" % url_for('today') + \
        "<br /><a href=\"%s\">Logout</a>" % url_for('logout')


@app.route("/today")
def today():
    today = datetime.now().strftime('%Y%m%d')
    info = moves.user_summary_daily(today, access_token=session['access_token'])
    res = ''
    if info[0]['summary'] is None:
        return res
    for activity in info[0]['summary']:
        if activity['activity'] == 'walking':
            res += 'Walking: %d steps<br />' % activity['steps']
        elif activity['activity'] == 'running':
            res += 'Running: %d steps<br />' % activity['steps']
        elif activity['activity'] == 'cycling':
            res += 'Cycling: %dm' % activity['distance']
    return res

app.secret_key = '\xfc$\xdd\xe9\x93\xc3s\x16\xca\x0e \xd6\x0e\xac\xa5\xdc\xe4B_I\x06\x1d\xf8d'

if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True)
