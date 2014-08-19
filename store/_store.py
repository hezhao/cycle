import redis

class Store():
    """
    Redis storage class
    """
    redis_url_local = 'redis://localhost:6379'
    
    def __init__(self, redis_url=redis_url_local):
        self.redis = redis.from_url(redis_url)

    def set_access_token():
        '''
        HSET 
        '''
        pass

    def set_user(self, user_id, access_token, refresh_token, first_name, last_name, email_address):
        '''
        HMSET user:[user_id] 'user_id' user_id 'access_token' access_token 'refresh_token' refresh_token 
                             'first_name' first_name 'last_name' last_name 'email_address' email_address
        '''
        m = {}
        m['user_id']        = user_id
        m['access_token']   = access_token
        m['refresh_token']  = refresh_token
        m['first_name']     = first_name
        m['last_name']      = last_name
        m['email_address']  = email_address

        return self.redis.hmset('user:%d' % user_id, m)
    
    def get_all_users(self):
        '''
        for every entry in redis, perform the following,
        HMGET user:[user_id] keys
        '''
        users = []
        keys = ['user_id', 'access_token', 'refresh_token', 'first_name', 'last_name', 'email_address']
        rkeys = self.redis.keys('*');
        for rkey in rkeys:
            values = self.redis.hmget(rkey, keys)
            user = dict(zip(keys, values))
            users.append(user)
        return users
