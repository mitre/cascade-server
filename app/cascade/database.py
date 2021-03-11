# NOTICE
#
# This software was produced for the U. S. Government
# under Basic Contract No. W15P7T-13-C-A802, and is
# subject to the Rights in Noncommercial Computer Software
# and Noncommercial Computer Software Documentation
# Clause 252.227-7014 (FEB 2012)
#
# (C) 2017 The MITRE Corporation.

import datetime

import dateutil.parser
import dateutil.tz
import mongoengine
from cryptography.fernet import Fernet
from itsdangerous import URLSafeSerializer
from mongoengine import EmbeddedDocument, Document
from mongoengine.fields import BaseField, StringField, DateTimeField
from mongoengine.errors import NotUniqueError
from pymongo import MongoClient

from app import settings


name = 'cascade2'

# This key will be set in server.py when loading
serializer = None  # type: URLSafeTimedSerializer
fernet = None  # type: Fernet


def connect():
    global serializer, fernet
    crypto_info = settings.load()['database']['crypto']
    mongo_host = settings.load()['database']['mongo'].get('host', '127.0.0.1')
    mongo_port = settings.load()['database']['mongo'].get('port', '27017')
    serializer = URLSafeSerializer(crypto_info['key'])
    fernet = Fernet(crypto_info['fernet'])
    mongoengine.connect(name, host=mongo_host, port=mongo_port, tz_aware=True)


def pymongo():
    mongo_host = settings.load()['database']['mongo'].get('host', '127.0.0.1')
    mongo_port = settings.load()['database']['mongo'].get('port', '27017')
    return MongoClient(host=mongo_host, port=mongo_port)[name]


class EncryptedStringField(mongoengine.StringField):
    # Create a token before encrypting the value, to avoid double encryption
    # The encrypted text is base64 so these characters will never show up in the text
    prefix = '$$$$:'

    def decrypt_value(self, value):
        if value is None or not value.startswith(self.prefix):
            return value
        return fernet.decrypt(str(value)[len(self.prefix):])

    def encrypt_value(self, value):
        if value is None or value.startswith(self.prefix):
            return value
        else:
            return self.prefix + fernet.encrypt(str(value))

    def to_mongo(self, value):
        return self.encrypt_value(value)

    def __set__(self, instance, value):
        encrypted_value = self.encrypt_value(value)
        super(EncryptedStringField, self).__set__(instance, encrypted_value)

    def prepare_query_value(self, op, value):
        return self.encrypt_value(value)

    def __get__(self, instance, owner):
        encrypted_value = super(EncryptedStringField, self).__get__(instance, owner)
        decrypted_value = self.decrypt_value(encrypted_value)
        return self.to_python(decrypted_value)


class TimeDeltaField(mongoengine.fields.BaseField):

    def validate(self, value):
        if isinstance(value, datetime.timedelta):
            pass
        elif isinstance(value, int) or isinstance(value, float):
            pass
        elif isinstance(value, str):
            # Attempt to convert it from a string
            self.from_str(value)
        else:
            raise mongoengine.ValidationError("type {} can't be converted to timedelta".format(type(value)))

    @staticmethod
    def from_str(value):
        # Convert everything
        negative = value.startswith('-')
        if negative:
            value = value[1:]
        hours, minutes, seconds = value.split(':')

        num_seconds = (float if '.' in seconds else int)(seconds)
        delta = datetime.timedelta(hours=int(hours), minutes=int(minutes), seconds=num_seconds)
        if negative:
            delta = -delta
        return delta

    def to_mongo(self, value):
        """ call the prepare_query_value code because this should basically do the same thing """
        return self.prepare_query_value(None, value)

    def to_python(self, value):
        """ Prepare python code before submitting it to mongo """
        if isinstance(value, datetime.timedelta):
            return value
        elif isinstance(value, str):
            return self.from_str(value)
        elif isinstance(value, (int, float)):
            return datetime.timedelta(seconds=value)

    def prepare_query_value(self, op, value):
        """ Prepare python code before submitting it for a query. Should have already passed validation """
        if isinstance(value, datetime.timedelta):
            value = value.total_seconds()

        elif isinstance(value, str):
            value = self.from_str(value).total_seconds()

        return value


class UniqueDocument(Document):
    meta = {'abstract': True, 'indexes': [dict(cls=False, fields=['uuid'], unique=True)]}
    uuid = StringField(unique=True)

    def __init__(self, *args, **kwargs):
        super(UniqueDocument, self).__init__(*args, **kwargs)
        if self.uuid is None:
            self.uuid = self.get_uuid()

    def uuid_time(self, key='time'):
        # Drop the microsecond granularity
        return datetime.datetime(*self[key].utctimetuple()[:-3])

    def get_uuid_tuple(self):
        raise NotImplementedError()

    def get_uuid(self):
        uuid_string = "-".join(str(_).lower() for _ in self.get_uuid_tuple())
        if hasattr(self, '_cls') and isinstance(self._cls, str):
            uuid_string = self._cls + "-" + uuid_string
        return uuid_string

    def existing(self):
        # grab the existing copy of the object from the database
        return type(self).objects.with_id(self.id) if self.id else type(self).objects(uuid=self.get_uuid()).first()

    @classmethod
    def get_existing(cls, *args, **kwargs):
        new_obj = cls(*args, **kwargs)
        return new_obj.existing()

    def exists(self):
        return self.existing() is not None

    @classmethod
    def update_existing(cls, **kwargs):
        # Create a new object to resolve the UUID to ObjectId
        new_obj = cls(**kwargs)
        existing_obj = new_obj.existing()

        if existing_obj is None:
            try:
                new_obj.save()
                return new_obj
            except NotUniqueError as e:
                new_obj.id = None
                # if a race condition occurs in python, and in object was created, then get that object and update it
                existing_obj = new_obj.existing()

        existing_obj.modify(**kwargs)
        return existing_obj

    def save(self, *args, **kwargs):
        # this is not recommended as it may overwrite changes and lead to race conditions
        try:
            return super(UniqueDocument, self).save(*args, **kwargs)
        except NotUniqueError:
            self.id = None
            existing = self.existing()
            if existing:
                self.id = existing.id
            return super(UniqueDocument, self).save(*args, **kwargs)


class DisjointSet(object):

    def __init__(self, items, links=None):  # , session):
        self.forest = {}  # id -> (event/result, parent id, rank)
        """
        :type items: List[Document]
        """
        if links is None:
            links = lambda x: x.links
        self._get_neighbors = links
        # self.session = session

        for item in items:
            self.forest[item.id] = (item, item.id, 0)

        # generate sets
        for item in items:
            for neighbor in links(item):
                self.union(item.id, neighbor.id)

        # for key, (item, item_id, index) in self.forest.items():
        #     for neighbor in self._get_neighbors(item):
        #        self.union(key, neighbor.id)

    # recursively search until you find a parent who is itself
    def find_root(self, item_id):
        try:
            item, parent_id, rank = self.forest[item_id]
        except KeyError as exc:
            pass

        if parent_id == item_id:
            return item, parent_id, rank
        else:
            return self.find_root(parent_id)

    def union(self, id1, id2):
        # if id1 not in self.forest or id2 not in self.forest:
        #     return

        item_1, parent_id_1, rank_1 = self.find_root(id1)
        item_2, parent_id_2, rank_2 = self.find_root(id2)

        #  Are not disjoint
        if parent_id_1 == parent_id_2:
            return

        if rank_1 < rank_2:
            # make index1 root a brother to index2 root
            self.forest[parent_id_1] = (item_1, parent_id_2, rank_1)
        elif rank_2 < rank_1:
            # make index2 root a brother to index1 root
            self.forest[parent_id_2] = (item_2, parent_id_1, rank_2)
        else:
            # make index2 root a child of index1 root, increase rank
            self.forest[parent_id_2] = (item_2, parent_id_1, rank_2)
            self.forest[parent_id_1] = (item_1, parent_id_1, rank_1 + 1)

    def clusters(self):
        clusters = {}

        for item_id, (event, parent_id, rank) in self.forest.items():
            root_item, root_id, root_rank = self.find_root(item_id)

            if clusters.get(root_id) is None:
                clusters[root_id] = []

            clusters[root_id].append(event)

        return clusters.values()


class DateRange(EmbeddedDocument):
    meta = {'allow_inheritance': True}
    start = BaseField()
    end = BaseField()

    @staticmethod
    def utcnow():
        return datetime.datetime.now(tz=dateutil.tz.tzutc())

    def constrain(self, start, end):
        raise NotImplementedError()

    @classmethod
    def get_range(cls, json_dict):
        mode = json_dict['mode']
        range_info = json_dict.get(mode, {})
        if mode == 'absolute':
            time_range = AbsoluteRange(**range_info)
        else:
            time_range = RelativeRange(**range_info)

        time_range.validate()
        return time_range

    def get_uuid_tuple(self):
        raise NotImplementedError


class AbsoluteRange(DateRange):
    start = DateTimeField()
    end = DateTimeField()

    def __init__(self, *args, **kwargs):
        super(AbsoluteRange, self).__init__(*args, **kwargs)
        if isinstance(self.start, str):
            self.start = dateutil.parser.parse(self.start)
        if isinstance(self.end, str):
            self.end = dateutil.parser.parse(self.end)

    def constrain(self, start, end):
        range_start = self.start
        range_end = self.end

        if range_end is None:
            range_end = self.utcnow()

        if start is None:
            constrained_start = range_start
        else:
            constrained_start = max(start, range_start)

        if end is None:
            constrained_end = range_end
        else:
            constrained_end = min(end, range_end)

        return constrained_start, constrained_end

    def get_uuid_tuple(self):
        return self.start.isoformat(), self.end.isoformat()


class RelativeRange(DateRange):
    # These must both be negative, because you can't have a relative range into the future!
    start = TimeDeltaField()
    end = TimeDeltaField(default=datetime.timedelta(seconds=0))

    @property
    def start_time(self):
        return self.utcnow() + self.start

    @property
    def end_time(self):
        return self.utcnow() + self.end

    def constrain(self, start, end):
        constrained_start = None
        constrained_end = None

        if start is None:
            constrained_start = self.start

        elif isinstance(start, datetime.datetime):
            # Compare the range end to the absolute time for comparison, but use as relative in search
            if start < self.start_time:
                constrained_start = self.start
            else:
                constrained_start = start

        elif isinstance(start, datetime.timedelta):
            constrained_start = max(start, self.start)

        if end is None:
            constrained_end = self.end

        elif isinstance(end, datetime.datetime):
            # Compare the range end to the absolute time for comparison, but use as relative in search
            if end > self.end_time:
                constrained_end = self.end
            else:
                constrained_end = end

        elif isinstance(end, datetime.timedelta):
            constrained_end = min(end, self.end)

        return constrained_start, constrained_end

    def get_uuid_tuple(self):
        return self.start.total_seconds(), None if self.end is None else self.end.total_seconds()