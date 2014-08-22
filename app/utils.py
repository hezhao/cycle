import json
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
        # print i, json.dumps(segment, indent=2)
        if is_cycling(segment):
            idx_cycling.append(i)
        else:
            pass
            # print i

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



