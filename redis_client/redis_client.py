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
        return self._decode(self.get(name))

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
        if isinstance(value, bool):
            if value:
                value = 'True'
            else:
                value = 'False'
        return self.set(name, value, ex=ex, px=px, nx=nx, xx=xx, keepttl=keepttl)

    # def mset_(self, mapping):
    #     """
    #     Sets key/values based on a mapping. Mapping is a dictionary of
    #     key/value pairs. Both keys and values should be strings or types that
    #     can be cast to a string via str().
    #     """
    #     items = []
    #     for pair in iteritems(mapping):
    #         items.extend(pair)
    #     return self.execute_command('MSET', *items)

    @staticmethod
    def dumps(message):
        """Convert to json with datetime safe encoder."""
        try:
            message = dumps(vars(message), cls=JSONDatetimeEncoder)
        except TypeError:
            message = dumps(message, cls=JSONDatetimeEncoder)
        return message

    @classmethod
    def decode(cls, message:bytes):
        """Decodes bytes to string, list, """
        message = cls._decode(message)
        if isinstance(message, list):
            message = [cls._decode(submessage) for submessage in message]
            return message[0], *message[1::]
        return message

    @classmethod
    def _decode(cls, message:bytes):
        """Decodes bytes to string."""
        if isinstance(message, bytes):
            message = message.decode('utf8')
        # message = cls.loads(message)
        return message

    @classmethod
    def loads(cls, message, recursive=False):
        """Converts json string to dict."""
        try:
            message = loads(message, cls=JSONDatetimeDecoder)
        except (JSONDecodeError, TypeError):
            # print('JSONDecodeError or TypeError')
            return message
        if recursive:
            return cls.loads(message)
        return message

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
    def __init__(self, *args, **kargs):
        JSONDecoder.__init__(self, object_hook=self.dict_to_object, *args, **kargs)

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
