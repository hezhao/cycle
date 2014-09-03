import redis

class Store():
    """
    Redis storage class
    """
    redis_url_local = 'redis://localhost:6379'
    
    def __init__(self, redis_url=redis_url_local):
        self.redis = redis.from_url(redis_url)


    def set_user(self, user_id, access_token, refresh_token, first_name, last_name, email_address, first_date):
        '''
        HMSET user:[user_id] 'user_id' user_id 'access_token' access_token 'refresh_token' refresh_token 
                             'first_name' first_name 'last_name' last_name 'email_address' email_address
                             'first_date' first_date
        '''
        m = {}
        m['user_id']        = user_id
        m['access_token']   = access_token
        m['refresh_token']  = refresh_token
        m['first_name']     = first_name
        m['last_name']      = last_name
        m['email_address']  = email_address
        m['first_date']     = first_date

        return self.redis.hmset('user:%d' % user_id, m)

    
    def get_all_users(self):
        '''
        HGETALL user:[user_id] keys
        '''
        users = []
        rkeys = self.redis.keys('user:*')
        for rkey in rkeys:
            user = self.redis.hgetall(rkey)
            users.append(user)
        return users


    def set_leaderboard(self, period, entries, timeout=60):
        '''
        HMSET  leaderboard:[period]:[user_id] entry
        EXPIRE leaderboard:[period]:[user_id] timeout
        RPUSH  leaderboard:[period] leaderboard:[period]:[user_id]
        EXPIRE leaderboard:[period] timeout
        '''
        for entry in entries:
            self.redis.hmset( 'leaderboard:%s:%s' % (period, entry.user_id), entry.__dict__)
            self.redis.expire('leaderboard:%s:%s' % (period, entry.user_id), timeout)
            self.redis.rpush( 'leaderboard:%s' % period,  'leaderboard:%s:%s' % (period, entry.user_id) )
        return self.redis.expire('leaderboard:%s' % period, timeout)


    def get_leaderboard(self, period):
        '''
        EXISTS  leaderboard:[period]
        LRANGE  leaderboard:[period] 0 -1
        HGETALL leaderboard:[period]:[user_id]
        '''
        entries = []
        if self.redis.exists('leaderboard:%s' % period):
            elements = self.redis.lrange('leaderboard:%s' % period, 0, -1)
            for e in elements:
                entry = self.redis.hgetall(e)
                entries.append(entry)
        return entries
        
