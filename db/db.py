from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class DB(object):
    __metaclass__ = Singleton

    def __init__(self):
        self._engine = create_engine('sqlite:///files//courses.db')
        self._base = declarative_base()
        self._base.metadata.bind = self._engine
        self._db_session = sessionmaker()
        self._db_session.bind = self._engine
        self._session = self._db_session()

    @property
    def session(self):
        return self._session

    @property
    def engine(self):
        return self._engine


# set default instance
db_instance = DB()
