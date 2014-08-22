import time

class Cycling():
    """
    Cycling data info class
    """

    (TO_WORK, FROM_WORK) = ('toWork', 'fromWork')

    def __init__(self, idx_segment=None, distance=None, duration=None, start_time=None, end_time=None, direction=None):
        self.idx_segment = idx_segment
        self.distance    = distance
        self.duration    = duration
        self.start_time  = start_time
        self.end_time    = end_time
        self.direction   = direction


    def __str__(self):
        info = {}
        info['idx_segment'] = self.idx_segment
        info['distance']    = self.distance
        info['duration']    = self.duration
        info['start_time']  = self.start_time
        info['end_time']    = self.end_time
        info['direction']   = self.direction

        return str(info)


    def formatted(self):
        '''
        TODO
        format cycling data
        duration: convert from seconds to HH:MM:SS
        distance: convert from meters to miles 
        '''
        info = {}
        meter2mile = 1609.34

        info['idx_segment'] = self.idx_segment
        info['duration']    = time.strftime('%H:%M:%S', time.gmtime(self.duration))
        info['distance']    = self.distance / meter2mile
        info['start_time']  = self.start_time
        info['end_time']    = self.end_time
        info['direction']   = self.direction

        return info
 
