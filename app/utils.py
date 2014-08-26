import re
import time
import calendar
from datetime import date, datetime, timedelta
from isoweek import Week
from flask import url_for
from cycling import Cycling

def segment_start_end(segment, res):
    res += 'Start Time: %s<br />' % segment['startTime']
    res += 'End Time: %s<br />' % segment['endTime']
    return res

def activity_start_end(activity, res):
    res += 'Start Time: %s<br />' % activity['startTime']
    res += 'End Time: %s<br />' % activity['endTime']
    return res

def activities_block(activity, res):
    res += 'Group: %s<br />' % activity['group']
    res = activity_start_end(activity, res)
    res += 'Duration: %d<br />' % activity['duration']
    res += 'Distance: %dm<br />' % activity['distance']

    if activity['group'] == 'walking':
        res += 'Walking: %d steps<br />' % activity['steps']
    elif activity['group'] == 'running':
        res += 'Running: %d steps<br />' % activity['steps']
    elif activity['group'] == 'cycling':
        res += 'Cycling: %d meters<br />' % activity['distance']
    elif activity['group'] == 'transport':
        print 'transport'
        res += 'Transport: %d meters<br />' % activity['distance']

    if 'calories' in activity:
        res += 'Calories: %d<br />' % activity['calories']
    if 'trackPoints' in activity:
        for track_point in activity['trackPoints']:
            res = trackPoint(track_point, res)
    return res

def place_block(segment, res):
    res += 'ID: %d<br />' % segment['place']['id']
    res += 'Type: %s<br />' % segment['place']['type']
    if segment['place']['type'] == 'foursquare':
        res += 'Foursquare ID: %s<br />' % segment['place']['foursquareId']
    if segment['place']['type'] != 'unknown':
        res += 'Name: %s<br />' % segment['place']['name']
    res += 'Location<br />'
    res += 'Latitude: %f<br />' % segment['place']['location']['lat']
    res += 'Longitude: %f<br />' % segment['place']['location']['lon']
    return res

def trackPoint(track_point, res):
    res += 'Latitude: %f<br />' % track_point['lat']
    res += 'Longitude: %f<br />' % track_point['lon']
    res += 'Time: %s<br />' % track_point['time']
    return res

def place(segment, res):
    res += 'Place<br />'
    res = segment_start_end(segment, res)
    res = place_block(segment, res)
    if 'activities' in segment:
        for activity in segment['activities']:
            res = activities_block(activity, res)
    res += '<br />'
    return res

def move(segment, res):
    res += 'Move<br />'
    res = segment_start_end(segment, res)
    for activity in segment['activities']:
        res = activities_block(activity, res)
    res += '<br />'
    return res

def move_from_place(idx_move, segments):
    '''
    find the previous place of a move in segments 
    '''
    # starting from idx_move-1, search all previous segments 
    # to find the first segment which is a place (since there
    #  can be multiple moves between places)
    assert segments[idx_move]['type'] == 'move'
    for i in range(idx_move-1, -1, -1):
        if segments[i]['type'] == 'place':
            return segments[i]
    return None
    

def move_to_place(idx_move, segments):
    '''
    find the following place of a move in segments 
    '''
    assert segments[idx_move]['type'] == 'move'
    for i in range(idx_move, len(segments)):
        if segments[i]['type'] == 'place':
            return segments[i]
    return None

def is_home(segment):
    '''
    identify if a segment is home
    '''
    if segment is None:
        return False
    if segment['type'] != 'place':
        return False
    if segment['place']['type'] == 'home':
        return True
    return False

def is_work(segment):
    '''
    identify if a segment is work
    '''
    if segment is None:
        return False
    if segment['type'] != 'place':
        return False
    if segment['place']['type'] == 'work':
        return True
    if 'name' in segment['place']:
        if segment['place']['name'].lower() == 'wieden + kennedy':
            return True
    return False

def is_cycling(segment):
    '''
    identify if a segment has cycling activity
    '''
    if segment is None:
        return False
    if segment['type'] != 'move':
        return False
    for activity in segment['activities']:
        if 'group' in activity:
            if activity['group'] == 'cycling':
                return True
    return False

def init_cycling(segment, idx_segment=None, direction=None):
    '''
    initialize a Cycling class instance from a segment 
    '''
    cycle = Cycling()
    assert segment['type'] == 'move'
    # assume only one cycling activity
    for activity in segment['activities']:
        if activity['group'] == 'cycling':
            cycle.idx_segment = idx_segment
            cycle.direction   = direction
            cycle.distance    = float(activity['distance'])
            cycle.duration    = float(activity['duration'])
            cycle.start_time  = activity['startTime']
            cycle.end_time    = activity['endTime']
    return cycle

def cycles_of_the_day(segments):
    '''
    return a list of Cycle class instances to/from work in a given day segments 
    '''
    idx_cycling = []
    cycles = []

    if segments is None:
        return cycles

    # find all moves that has cycling
    for i, segment in enumerate(segments):
        if is_cycling(segment):
            idx_cycling.append(i)

    # filter eligible cycling moves between home and work
    for i in idx_cycling:
        from_place = move_from_place(i, segments)
        to_place   = move_to_place(i, segments)
        if is_home(from_place) and is_work(to_place):
            cycle_to_work = init_cycling(segments[i], i, Cycling.TO_WORK)
            cycles.append(cycle_to_work)
        if is_work(from_place) and is_home(to_place):
            cycle_from_work = init_cycling(segments[i], i, Cycling.FROM_WORK)
            cycles.append(cycle_from_work)

    return cycles


def validate_period(period, first_date):
    '''
    make sure only period is  between first_date and today
    '''  
    today = datetime.now().strftime('%Y%m%d')

    # Day yyyyMMdd
    if type_of_period(period) == 'day':
        if period >= first_date and period <= today:
            return True
    
    # Week yyyy-Www
    elif type_of_period(period) == 'week':
        this_week = Week.thisweek()
        period_week = Week.fromstring(period)
        first_date_week = Week.withdate(datetime.strptime(first_date, '%Y%m%d'))
        if period_week >= first_date_week and period_week <= this_week:
            return True

    # Month yyyyMM
    elif type_of_period(period) == 'month':
        this_month       = datetime.now().strftime('%Y%m')
        period_month     = period[0:6]
        first_date_month = first_date[0:6]
        if period_month >= first_date_month and period_month <= this_month:
            return True
        
    return False


def type_of_period(period):
    '''
    determine the type of a period.
    e.g. 20140824 is a day
         201408   is a month
         2014-W34 is a week
    '''
    # regex for day, week and month format
    regex_day   = re.compile('^\d{8}$')
    regex_week  = re.compile('^\d{4}-W\d{1,2}$')
    regex_month = re.compile('^\d{6}$')

    # Day yyyyMMdd
    if regex_day.search(period):
        return 'day'
    # Week yyyy-Www
    elif regex_week.search(period):
        return 'week'
    # Month yyyyMM
    elif regex_month.search(period):
        return 'month'

    return None


def page_urls(period):
    '''
    return the next period.
    e.g. next period of 20140824 is 20140825
         next period of 201408   is 201409
         next period of 2014-W34 is 2014-W35
    '''

    page = dict()

    # 'Day', 'Week', 'Month' link to the current day/week/month 
    today             = datetime.now().strftime('%Y%m%d')
    this_week         = Week.thisweek().isoformat()[:4] + '-' +  Week.thisweek().isoformat()[4:]
    this_month        = datetime.now().strftime('%Y%m')
    page['day_url']   = url_for('views.leaderboard_period', period=today)
    page['week_url']  = url_for('views.leaderboard_period', period=this_week)
    page['month_url'] = url_for('views.leaderboard_period', period=this_month)

    
    if type_of_period(period) == 'day':
        # title 
        today             = datetime.strptime(period, '%Y%m%d')
        page['title']     = custom_strftime(today, '%a, %B {S} %Y')

        # 'prev' and 'next' links
        t                 = time.strptime(period, '%Y%m%d')
        today             = date(t.tm_year, t.tm_mon, t.tm_mday)
        nextday           = today + timedelta(1)
        prevday           = today + timedelta(-1)
        page['next_url']  = url_for('views.leaderboard_period', period=nextday.strftime('%Y%m%d'))
        page['prev_url']  = url_for('views.leaderboard_period', period=prevday.strftime('%Y%m%d'))
      
        return page
    
    elif type_of_period(period) == 'week':
        
        # title 
        page['title']     = datetime.strptime(period + '1', '%Y-W%W%w').strftime('Week %W, %Y')

        # 'prev' and 'next' links

        # begin_of_next_week = time.strptime('201435 1', '%Y%W %w')
        # use isoweek instead strptime('%W') since isoweek starts from week 1 
        # while strptime('%W') returns week number starting from week 0
        thisweek = Week.fromstring(period)
        nextweek = thisweek + 1
        # ISO 8610 format is "YYYYWww" while Moves API takes "YYYY-Www"
        page['next_url'] = url_for('views.leaderboard_period', period=nextweek.isoformat()[:4] + '-' + nextweek.isoformat()[4:])
        # next_text = 'Week ' + str(nextweek.week) + ', ' + str(nextweek.year)
        prevweek = thisweek -1
        page['prev_url'] = url_for('views.leaderboard_period', period=prevweek.isoformat()[:4] + '-' + prevweek.isoformat()[4:])
        # prev_text = 'Week ' + str(prevweek.week) + ', ' + str(prevweek.year)
        # return {'next_url': next_url, 'next_text': next_text, 'prev_url': prev_url, 'prev_text': prev_text} 

    elif type_of_period(period) == 'month':

        #title
        page['title'] = datetime.strptime(period, '%Y%m').strftime('%B %Y')

        # 'prev' and 'next' links
        t = time.strptime(period,'%Y%m')
        thismonth = date(t.tm_year, t.tm_mon, 1)
        nextmonth = add_months(thismonth, 1)
        prevmonth = add_months(thismonth, -1)
        page['next_url'] = url_for('views.leaderboard_period', period=nextmonth.strftime('%Y%m'))
        page['prev_url'] = url_for('views.leaderboard_period', period=prevmonth.strftime('%Y%m'))
      
    return page


def add_months(sourcedate, months):
    month = sourcedate.month - 1 + months
    year = sourcedate.year + month / 12
    # Note: python % results in a remainder 0<=r<divisor
    #       so the resulting month is alwasy greater than 0
    #       even if the input month is smaller than 0
    month = month % 12 + 1
    day = min(sourcedate.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def custom_strftime(t, format):
    return t.strftime(format).replace('{S}', str(t.day) + suffix(t.day))


def suffix(d):
    return 'th' if 11<=d<=13 else {1:'st',2:'nd',3:'rd'}.get(d%10, 'th')

