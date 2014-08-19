import os
from store import Store
from datetime import datetime, timedelta
from flask import Flask, url_for, request, session, redirect, render_template
from user_agents import parse
from moves import MovesClient


# flask
app             = Flask(__name__)
app.secret_key  = os.environ['FLASK_APP_SECRET']

# config vars
client_id       = os.environ['CLIENT_ID']
client_secret   = os.environ['CLIENT_SECRET']
redis_url       = os.environ['REDISTOGO_URL']

# class instances
moves           = MovesClient(client_id, client_secret)
store           = Store(redis_url)

@app.route('/')
def index():
    if 'access_token' not in session:
        return app.send_static_file('register.html')
    return redirect(url_for('home'))

@app.route('/', methods=['POST'])
def index_post():
    '''
    Return action from register page
    TODO: validate name and email entries
    '''
    session['first_name']       = request.form['first_name']
    session['last_name']        = request.form['last_name']
    session['email_address']    = request.form['email_address']

    # get user-agent 
    ua_string = request.headers.get('User-Agent')
    user_agent = parse(ua_string)
    
    # redirect to app from mobile browser, redirect to website and enter PIN from desktop browser
    oauth_return_url = url_for('oauth_return', _external=True)
    if user_agent.is_mobile:
        auth_url = moves.build_oauth_url(oauth_return_url, use_app=True)
    else:
        auth_url = moves.build_oauth_url(oauth_return_url, use_app=False)
    return redirect(auth_url)


@app.route('/oauth_return')
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

    # store each user's access_token, refresh_token, first_name, 
    # last_name, and email_address in redis hash
    store.set_user( session['user_id'], response['access_token'], response['refresh_token'], 
                    session['first_name'], session['last_name'], session['email_address'])

    return redirect(url_for('home'))


@app.route('/logout')
def logout():
    if 'access_token' in session:
        del(session['access_token'])
    return redirect(url_for('index'))


@app.route('/home')
def home():
    profile = moves.user_profile(access_token=session['access_token'])
    return render_template('home.html', first_name = session['first_name'])


@app.route('/day/<yyyyMMdd>')
def given_day(yyyyMMdd):
    info = moves.user_summary_daily(yyyyMMdd, access_token=session['access_token'])
    res = ''
    if info[0]['summary'] is None:
        return res
    for group in info[0]['summary']:
        if group['group'] == 'walking':
            res += 'Walking: %d steps<br />' % group['steps']
        elif group['group'] == 'running':
            res += 'Running: %d steps<br />' % group['steps']
        elif group['group'] == 'cycling':
            res += 'Cycling: %d meters<br />' % group['distance']
        elif group['group'] == 'transport':
            res += 'Transport: %d meters<br />' % group['distance']
    return res


@app.route('/today')
def today():
    today = datetime.now().strftime('%Y%m%d')
    return given_day(today)


@app.route('/leaderboard')
def leaderboard():
    '''
    Show user the leaderboard, no login is required
    '''
    pass


@app.route('/admin')
def admin():
    '''
    Export all user data to csv, login is required
    '''
    users = store.get_all_users()
    for user in users:
        access_token = user['access_token']
        profile = moves.user_profile(access_token=access_token)
        print profile['userId']
        
        # create download link to csv
        # user_id, first_name, last_name, email_address, start_time, end_time, activity_type
    return 'admin'



if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
