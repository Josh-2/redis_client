# cSpell:words mget, keepttl, mset
from datetime import datetime, date
from os import environ
from json import JSONEncoder, JSONDecoder, loads, dumps
from json.decoder import JSONDecodeError

from redis import Redis #, RedisError

class RedisClient(Redis):
    """ Redis helper class """
    def __init__(self, **kwargs):
        kwargs.setdefault('host', environ.get('REDIS_HOST', 'localhost'))
        kwargs.setdefault('port', int(environ.get('REDIS_PORT', 6379)))
        kwargs.setdefault('db', int(environ.get('REDIS_DB', 0)))
        kwargs.setdefault('password', environ.get('REDIS_PASSWORD'))
        super().__init__(**kwargs)
    #     self.__test_connection()

    # def __test_connection(self):
    #     try:
    #         self.ping()
    #     except RedisError:
    #         pass

    def get_(self, name):
        """
        Return the value at key ``name``, or None if the key doesn't exist
        """
        return self.decode(self.get(name))

    def mget_(self, keys, *args):
        """
        Returns a list of values ordered identically to ``keys``
        """
        return self.decode(self.mget(keys, *args))

    def set_(self, name, value,
            ex=None, px=None, nx=False, xx=False, keepttl=False):
        """
        Set the value at key ``name`` to ``value``

        ``ex`` sets an expire flag on key ``name`` for ``ex`` seconds.

        ``px`` sets an expire flag on key ``name`` for ``px`` milliseconds.

        ``nx`` if set to True, set the value at key ``name`` to ``value`` only
            if it does not exist.

        ``xx`` if set to True, set the value at key ``name`` to ``value`` only
            if it already exists.

        ``keepttl`` if True, retain the time to live associated with the key.
            (Available since Redis 6.0)
        """
        if not isinstance(value, str):
            value = self.encode(value)
        return self.set(name, value, ex=ex, px=px, nx=nx, xx=xx, keepttl=keepttl)

    def blpop_(self, keys, timeout=0):
        """
        LPOP a value off of the first non-empty list
        named in the ``keys`` list.

        If none of the lists in ``keys`` has a value to LPOP, then block
        for ``timeout`` seconds, or until a value gets pushed on to one
        of the lists.

        If timeout is 0, then block indefinitely.
        """
        return self.decode(self.blpop(keys, timeout))

    def rpush_(self, name, *values):
        "Push ``values`` onto the tail of the list ``name``"
        values = [self.encode(value) for value in values]
        return self.rpush(name, *values)

    def sadd_(self, name, *values):
        "Add ``value(s)`` to set ``name``"
        values = [self.encode(value) for value in values]
        return self.sadd(name, *values)

    def sismember_(self, name, value):
        "Return a boolean indicating if ``value`` is a member of set ``name``"
        value = self.encode(value)
        return self.sismember(name, value)

    def smembers_(self, name):
        "Return all members of the set ``name``"
        return self.decode(self.smembers(name))

    def smove_(self, src, dst, value):
        "Move ``value`` from set ``src`` to set ``dst`` atomically"
        value = self.encode(value)
        return self.smove(src, dst, value)

    def srem_(self, name, *values):
        "Remove ``values`` from set ``name``"
        values = [self.encode(value) for value in values]
        return self.srem(name, *values)

    def zrange_(self, name, start, end, desc=False, withscores=False,
               score_cast_func=float):
        """
        Return a range of values from sorted set ``name`` between
        ``start`` and ``end`` sorted in ascending order.

        ``start`` and ``end`` can be negative, indicating the end of the range.

        ``desc`` a boolean indicating whether to sort the results descendingly

        ``withscores`` indicates to return the scores along with the values.
        The return type is a list of (value, score) pairs

        ``score_cast_func`` a callable used to cast the score return value
        """
        return self.decode(self.zrange(name, start, end, desc=desc, withscores=withscores, score_cast_func=score_cast_func))

    @classmethod
    def encode(cls, value) -> str:
        """Encodes values with json"""
        if isinstance(value, list) or isinstance(value, tuple):
            value = [cls.encode(sub_value) for sub_value in value]
        try:
            value = dumps(vars(value), cls=JSONDatetimeEncoder)
        except TypeError:
            value = dumps(value, cls=JSONDatetimeEncoder)
        return value

    @classmethod
    def decode(cls, value:bytes):
        """Decodes bytes to string then json loads"""
        if isinstance(value, bytes):
            value = value.decode('utf8')
        if value is not None:
            try:
                value = loads(value, cls=JSONDatetimeDecoder)
            except (TypeError, JSONDecodeError):
                pass
        if isinstance(value, list) or isinstance(value, tuple):
            value = [cls.decode(sub_value) for sub_value in value]
        return value

class JSONDatetimeEncoder(JSONEncoder):
    """
    Encodes datetime as dict which is later decoded by JSONDatetimeDecoder.
    Attempts to encode a class using obj.to_dict()
    def to_dict(self):
        return {** self.__dict__}
    """
    def default(self, obj):
        if isinstance(obj, date):
            return {
                '__type__' : 'date',
                'year' : obj.year,
                'month' : obj.month,
                'day' : obj.day,
            }
        elif isinstance(obj, datetime):
            return {
                '__type__' : 'datetime',
                'year' : obj.year,
                'month' : obj.month,
                'day' : obj.day,
                'hour' : obj.hour,
                'minute' : obj.minute,
                'second' : obj.second,
                'microsecond' : obj.microsecond,
            }
        else:
            try:
                return JSONEncoder.default(self, obj)
            except TypeError:
                return self.nested_class(obj)

    @staticmethod
    def nested_class(obj):
        try:
            return dumps(vars(obj), cls=JSONDatetimeEncoder)
        except TypeError:
            pass

class JSONDatetimeDecoder(JSONDecoder):
    """Decodes datetime type from json encoded with JSONDatetimeEncoder."""
    def __init__(self, *args, **kwargs):
        JSONDecoder.__init__(self, object_hook=self.dict_to_object, *args, **kwargs)

    def dict_to_object(self, my_dict):
        if '__type__' not in my_dict:
            return my_dict
        obj_type = my_dict.pop('__type__')
        try:
            dateobj = date(**my_dict)
            return dateobj
        except:
            try:
                dateobj = datetime(**my_dict)
                return dateobj
            except:
                my_dict['__type__'] = obj_type
                return my_dict
