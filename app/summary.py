import time
from app import utils
from app.cycling import Cycling as Cycling

class Summary():
    '''
    Leaderboard entry data class
    '''

    def __init__(self, *args, **kwargs):
        
        # unformated
        self.user_id      = ''
        self.name         = ''
        self.distance     = 0.0
        self.duration     = 0.0
        self.commute_days = 0
        self.work_days    = 0
        self.inbound      = 0
        self.outbound     = 0
        self.new_user     = False

        # formatted for leaderboard
        self.miles        = 0.0
        self.duration_str = ''
        self.speed        = 0
        self.rate         = 0
        self.trips        = 0


        # fromstoryline()
        if len(args) == 3:
            storyline  = args[0]
            user       = args[1]
            first_date = args[2]
            self.summary_storyline(storyline, user, first_date)
            
        # invalid
        else:
            raise BaseException

    @classmethod
    def fromstoryline(cls, storyline, user, first_date):
        '''
        initilize Summary class from response of Moves storyline API
        '''
        return cls(storyline, user, first_date)

    def format(self):
        '''
        format cycling data as leaderboard entry, all units in leaderboard.html units(miles, hh:mm:ss, mph)
        '''
        # miles:        in miles (round up to 0.1)
        # duration_str: in HH:MM:SS
        # speed:        in mph (round up to 0.1)
        # rate:         in percentage (e.g. 100 for 100%)
        # trips:        integer (sum of inbound and outbound)
        meter2mile = 1609.34
        self.miles = self.distance / meter2mile
        if self.duration > 0:
            self.speed  = self.miles / (self.duration / 3600)

        # round up to 0.1
        self.miles   = round(self.miles, 1)
        self.speed   = round(self.speed, 1)

        self.duration_str = time.strftime('%H:%M:%S', time.gmtime(self.duration))
        self.trips        = self.inbound + self.outbound

        # return the cycling rate in percentage
        if self.work_days == 0:
            self.rate = 0
        else:
            self.rate = int(float(self.commute_days) / self.work_days * 100)

        return self

    def summary_storyline(self, storyline, user, first_date):
        '''
        calculate summary of the period from storyline, all units in Moves units (meter, second)
        '''

        self.user_id = user['user_id']
        self.name    = user['first_name'] + ' ' + user['last_name']

        for day in storyline:

            # find cycling commutes for the day
            segments = day['segments']
            cycles = utils.cycles_of_the_day(segments)
            is_commute_to_work_today = False
            is_commute_from_work_today = False

            # only count one commute per way even though there may be multiple cycling trips
            # in one direciton (considering stops), maximum two total commutes per day
            for c in cycles:
                self.distance += c.distance
                self.duration += c.duration
                if not is_commute_to_work_today and c.direction == Cycling.TO_WORK:
                    is_commute_to_work_today = True
                    self.inbound += 1
                elif not is_commute_from_work_today and c.direction == Cycling.FROM_WORK:
                    is_commute_from_work_today = True
                    self.outbound += 1

            # find the numer of days when commuting to/from work
            if len(cycles) > 0:
                self.commute_days += 1

            # find the number of days where workplace is in the storyline
            if segments is None:
                continue
            for segment in segments:
                if utils.is_work(segment):
                    self.work_days += 1
                    break

            # find if the user started using Moves during the storyline peirod
            if first_date == day['date']:
                self.new_user = True

        return self
