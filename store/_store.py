import redis

class Store():
    """redis storage class"""
    redis_url_local = 'redis://localhost:6379'
    
    def __init__(self, redis_url=redis_url_local):
        self.redis = redis.from_url(redis_url)
    
    def set_access_token(self, user_id, access_token):
        return self.redis.hset('user:%d' % user_id, 'access_token', access_token)

    def get_access_token(self, user_id):
        return self.redis.hget('user:%d' % user_id, 'access_token')

    def set_refresh_token(self, user_id, refresh_token):
        return self.redis.hset('user:%d' % user_id, 'refresh_token', refresh_token)

    def get_refresh_token(self):
        return self.redis.hget('user:%d' % user_id, 'refresh_token')

    def set_first_name(self, user_id, first_name):
        return self.redis.hset('user:%d' % user_id, 'first_name', first_name)

    def get_first_name(self, user_id):
        return self.redis.hget('user_%d' % user_id, 'first_name')

    def set_last_name(self, user_id, last_name):
        return self.redis.hset('user:%d' % user_id, 'last_name', last_name)

    def get_last_name(self, user_id):
        return self.redis.hget('user:%d' % user_id, 'last_name')

    def set_email_address(self, user_id, email_address):
        print email_address
        return self.redis.hset('user:%d' % user_id, 'email_address', email_address)

    def get_email_address(self, user_id):
        return self.redis.hget('user:%d' % user_id, 'email_address')
        