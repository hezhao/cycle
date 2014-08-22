import time
import utils
from cycling import Cycling as Cycling

class LeaderboardEntry():
    '''
    Leaderboard entry data class
    '''

    def __init__(self, user=None, storyline=None):
        self.user       = user
        self.storyline  = storyline

        self.name       = ''
        self.distance   = 0.0
        self.duration   = 0.0
        self.toWork     = 0
        self.fromWork   = 0
        self.nCommutes  = 0
        self.rate       = 0

        self.commute_days = 0
        self.work_days    = 0

        self.leaderboard_entry()
        
    def leaderboard_entry(self):
        '''
        format cycling data as leaderboard entry
        '''

        for day in self.storyline:
            
            meter2mile = 1609.34
            self.name  = self.user['first_name'] + ' ' + self.user['last_name']

            # find cycling commutes for the day
            segments = day['segments']
            cycles = utils.cycles_of_the_day(segments)

            # # prints
            # print self.user['user_id'], self.user['first_name'], self.user['last_name'], self.user['email_address']
            # for c in cycles:
            #     print c.formatted()
           
            # sum all trips for each user
            for c in cycles:
                self.distance += c.distance
                self.duration += c.duration
                if c.direction == Cycling.TO_WORK:
                    self.toWork += 1
                elif c.direction == Cycling.FROM_WORK:
                    self.fromWork += 1

            # format cycling data
            # distance: convert from meters to miles
            # duration: convert from seconds to HH:MM:SS
            self.distance   = round(self.distance / meter2mile, 1)
            self.duration   = time.strftime('%H:%M:%S', time.gmtime(self.duration))
            self.nCommutes  = self.toWork + self.fromWork
            
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

        # return the cycling rate in percentage
        if self.work_days == 0:
            self.rate = 0
        else:
            self.rate = int(self.commute_days / self.work_days * 100)

