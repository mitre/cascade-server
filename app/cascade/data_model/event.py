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

from mongoengine.base import TopLevelDocumentMetaclass
from mongoengine import DoesNotExist
from mongoengine.fields import (
    DateTimeField, DictField, ListField, ReferenceField, EmbeddedDocument, EmbeddedDocumentField,
    DynamicField, StringField, DecimalField
)

from app.cascade.database import UniqueDocument
from app.cascade.data_model.host import Host
from .query import QueryTerm, CompareString, FieldQuery, EmptyQuery, EmbeddedQueryTerm

utc_tz = datetime.tzinfo(None, 0)


event_lookup = {}
""":type: dict[str, DataModelEventMeta | DataModelEvent] """


class EventState(EmbeddedDocument):
    meta = {'allow_inheritance': True}
    # Expose these fields now for indexing
    hostname = DynamicField()
    ppid = DynamicField()
    pid = DynamicField()
    fqdn = DynamicField()


class DataModelEventMeta(TopLevelDocumentMetaclass):
    """ This metaclass is to control the creation of all DataModelEvent subclasses.
    It takes several variables and generates class properties, etc. based off of them.

    : var fields: A list of fields for the data model object. Each field becomes a valid property that maps to
                  that property.
    : var actions: A list of all actions that can be performed by/on/to the object.
    : var identifiers: A list of the fields that uniquely identify an the object when paired with
        the event time and the host on which the event occurred.
    """
    def __new__(mcs, name, bases, dct):
        """ Creates new properties that map to the attributes.

        """
        state_cls = type(name + 'State', (EventState, ), {f: DynamicField() for f in dct['fields']})
        dct['state'] = EmbeddedDocumentField(state_cls)
        dct['object_type'] = StringField(default=dct['object_name'], choices=[dct['object_name']])
        dct['actions'] = tuple(sorted(dct.pop('actions', [])))
        dct['fields'] = tuple(sorted(dct.pop('fields', [])))
        new_cls = super(DataModelEventMeta, mcs).__new__(mcs, name, bases, dct)

        # Update the list of all objects so that the class can be mentioned by the data model name
        if dct['object_name']:
            event_lookup[dct['object_name']] = new_cls
        return new_cls


class LabeledLink(EmbeddedDocument):
    event = ReferenceField('DataModelEvent')
    label = StringField(required=True)


# python3 looks like:
# class HostSource(dict, metaclass=MetaSource)
class DataModelEvent(UniqueDocument):
    """ This class refers to any event in the FMX Data Model as described in the Cyber Analytics Repository
    (https://car.mitre.org/wiki/Data_Model). The event consists of an object type, an action performed by or on
    that object (often refers to a state change), and a set of fields.

    Objects can be causally related by connecting them with links, known as pivots.

    :var name: Name of the Data Model object (as in CAR)
    :var actions: list of the possible actions for the object
    :var fields: list of all acceptable fields for the object
    :var identifiers: list of the identifying fields for an event (given hostname, object, action and time)
    """
    __metaclass__ = DataModelEventMeta
    meta = {
        'allow_inheritance': True,
        'abstract': False,
        'indexes': [
            dict(cls=False, fields=['time']),
            dict(cls=False, fields=['action']),
            dict(cls=False, fields=['object_type']),
            dict(cls=False, fields=['host']),
            # dict(cls=False, fields=['uuid'], unique=True),
            dict(cls=False, fields=['state.pid']),
            dict(cls=False, fields=['state.ppid']),
            dict(cls=False, fields=['state.hostname'])
        ]
    }

    # Specify a fallback/ for class properties, etc.
    # These will be updated via the metaclass, but documenting them here is helpful for autocompletion in IDEs

    # Mongo schema definition
    action = StringField(required=True)
    state = EmbeddedDocumentField(EventState)
    time = DateTimeField()
    discovered_time = DateTimeField(default=datetime.datetime.utcnow)
    sessions = ListField(ReferenceField('Session'))
    links = ListField(ReferenceField('self'))
    labeled_links = ListField(EmbeddedDocumentField(LabeledLink))
    reverse_links = ListField(ReferenceField('self'))
    labeled_reverse_links = ListField(EmbeddedDocumentField(LabeledLink))
    host = ReferenceField('Host')
    metadata = DictField()
    uuid = StringField(unique=True)
    object_type = StringField()
    confidence = DecimalField(default=0.0)

    # These should be implemented by the subclass
    object_name = str()
    actions = tuple()
    fields = tuple()
    identifiers = tuple()

    def __init__(self, action, **kwargs):
        if isinstance(kwargs.get('state'), dict):
            state = kwargs['state']
            if 'fqdn' in state and 'hostname' not in state:
                state['hostname'] = state['fqdn'].split('.')[0]

            # Remove non-matching fields
            kwargs['state'] = {k: v for k, v in state.items() if k in self.fields}

        super(DataModelEvent, self).__init__(action=action, **kwargs)

        if self.uuid is None:
            self.uuid = self.get_uuid()

    def get_uuid_tuple(self):
        """ Generate an identifier string that is unique for this event. It depends on a
        set of fixed fields, such as the object name, action and host it occurred on. Additionally, it
        is generated from a set of class specific fields, described in the property 'identifiers'.

        :return: a string of a number that is unique for this DataModelEvent
        :rtype: str
        """
        # Drop the microsecond granularity
        utc_time = datetime.datetime(*self.time.utctimetuple()[:-3])
        loose_time = utc_time.isoformat()
        fixed_identifiers = (self.state.hostname, type(self).object_name, self.action, loose_time)
        identifiers = fixed_identifiers + tuple(self.state[_] for _ in self.identifiers)
        return identifiers

    @classmethod
    def search(cls, action=None, expression=EmptyQuery, **kwargs):
        """ Create a search query for this DataModel object. Given an expression as input (either a set of
        field requirements) or another search query. This function places query in the context of a DataModelEvent.

        :param kwargs: Field requirements (keys and values)
        :param action: Data model action for the specified object
        :type expression: QueryTerm
        :rtype: DataModelQuery
        """

        if len(kwargs):
            for name, value in kwargs.items():
                assert name in cls.fields
                if isinstance(value, CompareString):
                    expression &= value.compare(name)
                else:
                    expression &= (FieldQuery(name) == value)

        return DataModelQuery(cls, action, query=expression)

    def update_host(self):
        try:
            host = self.host
        except DoesNotExist:
            host = None
        hostname = self.state.hostname.upper()

        if not isinstance(host, Host):
            host = Host.update_existing(hostname=hostname)
            self.modify(host=host)

        if self.state.fqdn is not None and host.fqdn is None:
            host.update(fqdn=self.state.fqdn)

        elif host.fqdn is not None and self.state.fqdn is None:
            self.modify(state__fqdn=host.fqdn.upper())

        if 'user' in self.fields and self and self.state.user:
            host.update(add_to_set__users=self.state.user)

    def save(self, *args, **kwargs):
        status = super(DataModelEvent, self).save(*args, **kwargs)
        self.update_host()
        return status

    @classmethod
    def update_existing(cls, action, **kwargs):
        # Create a new object to resolve the UUID to ObjectId
        kwargs.pop('host', None)
        return super(DataModelEvent, cls).update_existing(action=action, **kwargs)

    def __repr__(self):
        """ Display a representation of this DataModelEvent that can be reproduced with an eval statement.
        Currently, it just returns the class name (object), action, and the set of fields.
        """
        return "{}(action={}, state={})".format(type(self).__name__, repr(self.action), self.state.to_json())

    __str__ = __repr__


class InvalidFieldError(KeyError):
    pass


class InvalidActionError(ValueError):
    pass


class InvalidObjectError(ValueError):
    pass


class DataModelQuery(EmbeddedQueryTerm):
    """ Forces a query (field comparisons, boolean operations, etc.) to be restricted to the context
    of a data model object and event.
    :type object: DataModelEvent | DataModelEventMeta object
    """
    object_name = StringField(db_field='object')
    action = StringField()
    query = EmbeddedDocumentField(EmbeddedQueryTerm)

    def __init__(self, cls=None, action=None, **kwargs):
        if cls is not None:
            kwargs['object_name'] = cls.object_name
            self.object = cls
        kwargs['action'] = action
        super(DataModelQuery, self).__init__(**kwargs)
        if cls is None:
            event_cls = event_lookup.get(self.object_name, None)
            if event_cls is None:
                raise InvalidObjectError()
            self.object = event_cls

        if action not in self.object.actions:
            raise InvalidActionError()
        if any(field not in self.object.fields for field in self.get_fields()):
            raise InvalidFieldError("Unknown field for DataModelEvent {}".format(self.object.object_name))

    def operation(self, other=None, operator=None):
        if isinstance(other, DataModelQuery):
            assert other.object == self.object and other.action == self.action
            other = other.query
        return DataModelQuery(self.object, self.action, query=self.query.operation(other, operator))

    def get_fields(self):
        return self.query.get_fields()

    def __repr__(self):
        return '{}({}, {}, expression={})'.format(
            type(self).__name__, repr(self.object.object_name), repr(self.action), self.query
        )

    def compare(self, event):
        return self.query.compare(event)
    __str__ = __repr__
