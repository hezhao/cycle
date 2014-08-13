from flask import Flask, url_for, request, session, redirect
from moves import MovesClient
from datetime import datetime, timedelta
import os
# import _keys

app = Flask(__name__)

# client_id = '3nZfgFy7wdzXNp9wd2PnglvysqzJUcox'
# client_secret = 'QPasM3H4_5iX91WJSitTOBi6aRHmByu4s38t9_2YewBDy_tYVT0LKFhEc8Bj4mUn'
client_id = os.environ['CLIENT_ID']
client_secret = os.environ['CLIENT_SECRET']

Moves = MovesClient(client_id, client_secret)

access_token = '2bE1LPx7l41a8IJ8YKhA9Fe15i12ZbaXs29DMdhhRs6MfzGbkCNw7315ELl4lIlJ'
user_id = '66863717373915380'

@app.route("/")
def index():
    if 'access_token' not in session:
        oauth_return_url = url_for('oauth_return', _external=True)
        auth_url = Moves.build_oauth_url(oauth_return_url)
        return 'Authorize this application: <a href="%s">%s</a>' % \
            (auth_url, auth_url)
    return redirect(url_for('show_info'))

@app.route("/myinfo")
def myinfo():
    profile = Moves.user_profile(access_token=access_token)
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
    response = Moves.get_oauth_token(code, redirect_uri=oauth_return_url)
    print response
    session['access_token'] = response['access_token']
    session['refresh_token'] = response['refresh_token']
    return redirect(url_for('show_info'))


@app.route('/logout')
def logout():
    if 'access_token' in session:
        del(session['access_token'])
    return redirect(url_for('index'))


@app.route("/info")
def show_info():
    profile = Moves.user_profile(access_token=session['access_token'])
    response = 'User ID: %s<br />First day using Moves: %s' % \
        (profile['userId'], profile['profile']['firstDate'])
    return response + "<br /><a href=\"%s\">Info for today</a>" % url_for('today') + \
        "<br /><a href=\"%s\">Logout</a>" % url_for('logout')


@app.route("/today")
def today():
    today = datetime.now().strftime('%Y%m%d')
    info = Moves.user_summary_daily(today, access_token=session['access_token'])
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
