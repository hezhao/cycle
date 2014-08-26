# TODO
# - ranking javascript
# - admin dump to csv
# - use refresh token when access token is expired
# ##############################################
# - save user['profile']['first_date'] to redis
# - save all leaderboard entries into one data structure in redis
# - read leaderboard entries from redis 
# - flask background thread to update leader board every hour
# - reduce use of moves api (0.5s per request)
# - reduce use of redis api (0.1s per operation)

import os
import json
from store import Store
from datetime import datetime
from flask import Blueprint, url_for, request, session, redirect, render_template
from user_agents import parse
from moves import MovesClient
import utils
from entry import LeaderboardEntry

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
    response = moves.get_oauth_token(code, redirect_uri=oauth_return_url)
    
    # store access_token and user_id in session
    session['access_token'] = response['access_token']
    session['user_id'] = response['user_id']

    # store each user's access_token, refresh_token, first_name, 
    # last_name, and email_address in redis hash
    store.set_user( session['user_id'], response['access_token'], response['refresh_token'], 
                    session['first_name'], session['last_name'], session['email_address'])

    return redirect(url_for('.home'))


@views.route('/logout')
def logout():
    if 'access_token' in session:
        del(session['access_token'])
    return redirect(url_for('.index'))


@views.route('/home')
def home():
    return render_template('home.html', first_name=session['first_name'])


# @views.route('/day/<yyyyMMdd>')
# def given_day(yyyyMMdd):
#     info = moves.user_summary_daily(yyyyMMdd, access_token=session['access_token'])
#     res = ''
#     if info[0]['summary'] is None:
#         return res
#     for group in info[0]['summary']:
#         if group['group'] == 'walking':
#             res += 'Walking: %d steps<br />' % group['steps']
#         elif group['group'] == 'running':
#             res += 'Running: %d steps<br />' % group['steps']
#         elif group['group'] == 'cycling':
#             res += 'Cycling: %d meters<br />' % group['distance']
#         elif group['group'] == 'transport':
#             res += 'Transport: %d meters<br />' % group['distance']
#     return res


# @views.route('/today')
# def today():
#     today = datetime.now().strftime('%Y%m%d')
#     return given_day(today)


# @views.route('/storyline/<yyyyMMdd>')
# def storyline(yyyyMMdd):
#     info = moves.user_storyline_daily(yyyyMMdd, trackPoints={'false'}, access_token='7Aryo5zL2i62OO7OJNvE3p4K0K2vDVS1NGVKpSDKFy5Miy464S0FCngdNE6j1m9N')
#     print info[0]['date']
#     segments = info[0]['segments']
#     # print json.dumps(segments, indent=2)
#     res = ''
#     for segment in segments:
#         if segment['type'] == 'place':
#             res = utils.place(segment, res)
#         elif segment['type'] == 'move':
#             res = utils.move(segment, res)
#         res += '<hr>'
#     return res


@views.route('/leaderboard')
def leaderboard():
    this_month = datetime.now().strftime('%Y%m')
    return leaderboard_period(this_month)


@views.route('/leaderboard/<period>')
def leaderboard_period(period):
    '''
    Show user the daily leaderboard, no login is required
    '''
    entries = []
    users = store.get_all_users()
    for user in users:

        # TODO
        # get rid of this by storing frist_date into redis
        ###################################################
        access_token = user['access_token']
        profile = moves.user_profile(access_token=access_token)
        first_date = profile['profile']['firstDate']
        ###################################################

        # validate period for user
        if utils.validate_period(period, first_date) is False:
            continue

        # get user info for the period (day/week/month)
        storyline = moves.user_storyline_daily(period, trackPoints={'false'}, access_token=access_token)

        # sum all trips of the peridod (day/week/month) for each user
        leaderboard_entry = LeaderboardEntry(user, first_date, storyline)
        entries.append(leaderboard_entry)

    # build up previous and next links
    urls = utils.page_urls(period)
    return render_template('leaderboard.html', entries=entries, urls=urls)



@views.route('/admin')
def admin():
    '''
    Export all user data to csv, login is required
    '''
    users = store.get_all_users()
    for user in users:
        access_token = user['access_token']
        print user['user_id'], user['first_name'], user['last_name'], user['email_address']
        
        # create download link to csv
        # user_id, first_name, last_name, email_address, start_time, end_time, distance, duration, #commutes (2x a day)
    return 'admin'
