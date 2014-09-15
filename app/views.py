# TODO
# - redis cloud daily backup
# - making sure wk.com user
# - Parse SDK user profile
# - background thread query 120 users per minute (rate limit: 120 requests per minute / 4000 requests per hour)
# - admin select from to dates dump to csv (first colume is people)
# - 1st 2nd 3rd Prizes

import os
import json
from store import Store
from datetime import datetime
from flask import Blueprint, url_for, request, Response, session, redirect, render_template
from functools import wraps
from user_agents import parse
from moves import MovesClient, MovesAPIError
import utils
from summary import Summary


# config vars
client_id       = os.environ['CLIENT_ID']
client_secret   = os.environ['CLIENT_SECRET']
redis_url       = os.environ['REDISTOGO_URL']

# class instances
moves           = MovesClient(client_id, client_secret)
store           = Store(redis_url)
views           = Blueprint('views', __name__)


@views.route('/')
def index():
    return leaderboard()


@views.route('/register')
def register():
    if 'access_token' not in session:
        return render_template('register.html')
    return redirect(url_for('.home'))


@views.route('/register', methods=['POST'])
def index_post():
    '''
    Return action from register page
    '''
    session['first_name']       = request.form['first_name']
    session['last_name']        = request.form['last_name']
    session['email_address']    = request.form['email_address']

    # get user-agent 
    ua_string = request.headers.get('User-Agent')
    user_agent = parse(ua_string)
    
    # redirect to app from mobile browser, redirect to website and enter PIN from desktop browser
    oauth_return_url = url_for('.oauth_return', _external=True)
    if user_agent.is_mobile:
        auth_url = moves.build_oauth_url(oauth_return_url, use_app=True)
    else:
        auth_url = moves.build_oauth_url(oauth_return_url, use_app=False)
    return redirect(auth_url)


@views.route('/oauth_return')
def oauth_return():
    error = request.values.get('error', None)
    if error is not None:
        return error
    oauth_return_url = url_for('.oauth_return', _external=True)
    code = request.args.get("code")
    response = moves.get_oauth_token(grant_type='authorization_code', code=code, redirect_uri=oauth_return_url)
    
    # store access_token and user_id in session
    session['access_token'] = response['access_token']
    session['user_id']      = response['user_id']

    # find first_date from GET /user/profile
    profile = moves.user_profile(access_token=session['access_token'])
    first_date = profile['profile']['firstDate']

    # store each user's access_token, refresh_token, first_name, 
    # last_name, email_address, and first_date in redis hash
    store.set_user( session['user_id'], response['access_token'], response['refresh_token'], 
                    session['first_name'], session['last_name'], session['email_address'], first_date)

    return redirect(url_for('.home'))


@views.route('/logout')
def logout():
    if 'access_token' in session:
        del(session['access_token'])
    return redirect(url_for('.index'))


@views.route('/home')
def home():
    return render_template('home.html', first_name=session['first_name'])


@views.route('/storyline/<yyyyMMdd>')
def storyline(yyyyMMdd):
    info = moves.user_storyline_daily(yyyyMMdd, trackPoints={'false'}, access_token='access_token')
    print info[0]['date']
    segments = info[0]['segments']
    # print json.dumps(segments, indent=2)
    res = ''
    for segment in segments:
        if segment['type'] == 'place':
            res = utils.place(segment, res)
        elif segment['type'] == 'move':
            res = utils.move(segment, res)
        res += '<hr>'
    return res


@views.route('/leaderboard')
def leaderboard():
    this_month = datetime.now().strftime('%Y%m')
    return leaderboard_period(this_month)


@views.route('/leaderboard/<period>')
def leaderboard_period(period):
    '''
    Show user the daily leaderboard, no login is required
    '''

    # try finding cache in Redis first
    entries = store.get_leaderboard(period)
    
    # if Redis returns empty and cache not found
    if not entries:

        # form leaderboard from Moves API 
        entries = get_leaderboard_moves(period)

        # cache leaderboard for 30min into Redis
        store.set_leaderboard(period, entries, timeout=1800)

    # build up previous and next links
    urls = utils.page_urls(period)
    return render_template('leaderboard.html', entries=entries, urls=urls)


def validate_access_token(user, access_token):
    '''
    return True if access token is valid.
    return True and set new access token if expired.
    return False if user revoked app.
    '''
    # try getting access token info
    try:
        # Moves: GET /oauth/v1/tokeninfo
        moves.tokeninfo(access_token)
        return True

    # current access token is invalid
    except MovesAPIError:

        # try getting access token in case expired
        refresh_token = user['refresh_token']
        try:
            # user token expired, set new access token and refresh token
            response = moves.get_oauth_token(grant_type='refresh_token', refresh_token=refresh_token)
            new_access_token  = response['access_token']
            new_refresh_token = response['refresh_token']
            store.set_user( user['user_id'], new_access_token, new_refresh_token, 
                            user['first_name'], user['last_name'], user['email_address'], user['first_date'])
            return True

        # user has revoked app, remove user in Redis
        except MovesAPIError:
            store.delete_user(user['user_id'])
            return False


def get_leaderboard_moves(period):
    '''
    return leaderboard entries for period from Moves storyline API
    Moves: GET /user/storyline/daily (period)
    '''
    entries = []
    users = store.get_all_users()

    for user in users:

        access_token = user['access_token']
        first_date   = user['first_date']

        # validate user access_token
        if validate_access_token(user, access_token) is False:
            continue

        # validate period for user
        if utils.validate_period(period, first_date) is False:
            continue

        # Moves: GET /user/storyline/daily (day/week/month)
        storyline = moves.user_storyline_daily(period, trackPoints={'false'}, access_token=access_token)

        # sum all trips of the period (day/week/month) for each user
        summary = Summary.fromstoryline(storyline, user, first_date)
        entry = summary.format()
        entries.append(entry)
    
    return entries


def validate_admin(username, password):
    return username == 'wkcycle' and password == 'supermegabonus'


def admin_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not validate_admin(auth.username, auth.password):
            return Response(
                'Could not verify your access level for that URL.\n'
                'You have to login with proper credentials', 
                401, {'WWW-Authenticate': 'Basic realm="Login Required"'})
        return f(*args, **kwargs)
    return decorated


@views.route('/admin')
@admin_auth
def admin():
    '''
    Export all user data of selected day range to csv, login is required
    '''
    return render_template('admin.html')
