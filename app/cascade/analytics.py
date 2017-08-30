# NOTICE
#
# This software was produced for the U. S. Government
# under Basic Contract No. W15P7T-13-C-A802, and is
# subject to the Rights in Noncommercial Computer Software
# and Noncommercial Computer Software Documentation
# Clause 252.227-7014 (FEB 2012)
#
# (C) 2017 The MITRE Corporation.

from database import UniqueDocument
from data_model.query import QueryTerm, EmbeddedQueryTerm
from data_model.event import DataModelEvent, DataModelQuery, event_lookup
from .attack import TechniqueMapping
from mongoengine.document import Document, EmbeddedDocument, DynamicDocument
from mongoengine.fields import (
    EmbeddedDocumentField, DictField, StringField, ListField, BooleanField, ReferenceField, DateTimeField
)
from cluster import HierarchicalCluster


class ObjectMapping(EmbeddedDocument):
    object_name = StringField(db_field='object')
    action = StringField()
    # Key is target field (of the data model),  and the Value is the field from the output
    field_map = DictField(db_field='fields')

    @property
    def object_type(self):
        return event_lookup[self.object_name]

    def is_mappable(self, state):
        return all(v in state for k, v in self.field_map.items())

    def from_result(self, state):
        return {k: state[v] for k, v in self.field_map.items()}


class Analytic(Document):
    """
    :param str name: The name of the analytic. All characters are valid
    :param List[TechniqueMapping] coverage: A list of all of technique, tactic pairs to be detected
    :param bool enabled: Enabled/disabled status of the analytic
    """
    # define some constants
    FIRST_PASS = 'first-pass'
    SECOND_PASS = 'second-pass'
    REALTIME = 'realtime' # not-implemented
    IDENTIFY_ONLY = 'identify-only'
    IDENTIFY_ONLY_NO_BASELINE = 'identify-only-no-baseline'

    modes = [FIRST_PASS, SECOND_PASS, REALTIME, IDENTIFY_ONLY, IDENTIFY_ONLY_NO_BASELINE]

    meta = {'allow_inheritance': True}
    coverage = ListField(EmbeddedDocumentField(TechniqueMapping))
    description = StringField()
    enabled = BooleanField(default=True)
    name = StringField(required=True, unique=True)
    mapped_events = ListField(EmbeddedDocumentField(ObjectMapping))
    mode = StringField(choices=modes)

    @property
    def baseline(self):
        return AnalyticBaseline.objects(analytic=self).first()

    def extract_events(self, result):
        raise NotImplementedError()

    def __repr__(self):
        return '{}(name={})'.format(type(self).__name__, repr(self.name))

    __str__ = __repr__


class ExternalAnalytic(Analytic):
    """
    :param List[str] fields: A list of all of the fields to be expected in each row of output
    :param List[ObjectMapping] mapped_objects: A list of all of the mapped objects
    :param str query_name: The name of the query saved on the target platform (i.e. Splunk)
    :param str car: Optional. The corresponding CAR analytic (car.mitre.org)
    :param str car_summary: Optional. The summary name of the CAR analytic
    :param str platform: The target platform (Splunk, ElasticSearch, etc.)
    """
    fields = ListField(StringField())
    query_name = StringField()
    car = StringField()
    car_summary = StringField()
    platform = StringField()

    def extract_events(self, result):
        state = result['state']

        # Generalize this capability for CASCADE analytics as well
        for mapping in self.mapped_events:
            object_type = mapping.object_type
            action = mapping.action
            if mapping.is_mappable(state):
                fields = mapping.from_result(state)
                # return a list of DataModelQuery objects (which will be run as jobs)
                yield object_type.search(action, **fields)


class CascadeAnalytic(QueryTerm, Analytic):
    """ An analytic is a higher level abstraction and maps to an ATT&CK technique.

    :param DataModelQuery query: The CASCADE data model query objects
    :param str platform: Statically set to "CASCADE"
    """
    platform = StringField(default="CASCADE")
    query = EmbeddedDocumentField(EmbeddedQueryTerm)
    query_text = StringField()

    def __init__(self, *args, **kwargs):
        super(CascadeAnalytic, self).__init__(*args, **kwargs)
        # create the mapped events list out of the query if it isn't present
        if self.mapped_events is None and isinstance(self.query, DataModelQuery):
            self.modify(mapped_events=[ObjectMapping(object_name=self.query.object_name, action=self.query.action)])

    @property
    def fields(self):
        fields = set()
        for mapped_event in self.mapped_events:
            fields.update(mapped_event.object_type.fields)
        return fields

    def compare(self, event):
        return self.query.compare(event)

    def prep_value(self):
        return AnalyticReference(analytic=self)

    def extract_events(self, result):
        # TODO: Support sophisticated analytics > 1 event
        query = self.query

        if isinstance(self.query, DataModelQuery):
            event_class = self.query.object
            event_action = self.query.action
            # yield the CASCADE objects
            yield event_class.update_existing(event_action, **result)
        else:
            raise NotImplementedError("Unable to extract data model event from analytic")


class AnalyticReference(EmbeddedQueryTerm):
    analytic = ReferenceField(CascadeAnalytic)

    @classmethod
    def with_name(cls, name):
        analytic = Analytic.objects(name=name).first()
        return AnalyticReference(analytic=analytic)

    def compare(self, event):
        return self.query.compare(event)

    @property
    def query(self):
        return self.analytic

    def __repr__(self):
        return '{}({})'.format(type(self).__name__, self.analytic)

    __str__ = __repr__


class AnalyticResult(UniqueDocument):
    analytic = ReferenceField(Analytic)
    session = ReferenceField('Session')
    events = ListField(ReferenceField(DataModelEvent), default=[])
    result = DictField()
    time = DateTimeField()

    @staticmethod
    def _dict_tuple(d):
        return tuple("{}:{}".format(k, v) for k, v in sorted(d.items()))

    def get_uuid_tuple(self):
        analytic = self.analytic
        base_tuple = (analytic.id, self.session.id)
        if isinstance(analytic, CascadeAnalytic):
            return base_tuple + tuple(_.id for _ in self.events)
        elif isinstance(analytic, ExternalAnalytic):
            result = self.result
            state = result.get('state', {})
            mapping_tuple = tuple((mapping.object_name, mapping.action) + self._dict_tuple(mapping.from_result(state))
                                  for mapping in analytic.mapped_events)
            return base_tuple + mapping_tuple


class AnalyticBaseline(HierarchicalCluster):
    analytic = ReferenceField(Analytic)
    time_range = EmbeddedDocumentField('DateRange')

    def optimize(self):
        results = self.recover_events()
        self.cluster_events(results, max_children=16)

    def cluster_events(self, events, *args, **kwargs):
        ignored = {'pid', 'ppid', 'hash'}
        unless = (4, '4', None, 'None', '')
        # for each event, strip out the ignored keys
        new_events = [{k: v for k, v in _.items()
                       if (k.split('_').pop() not in ignored) and v not in unless
                       } for _ in events]
        return super(AnalyticBaseline, self).cluster_events(new_events, *args, **kwargs)


class AnalyticConfiguration(EmbeddedDocument):
    mode = StringField(choices=Analytic.modes)
    analytic = ReferenceField(Analytic)


class AnalyticConfigurationList(Document):
    analytics = ListField(EmbeddedDocumentField(AnalyticConfiguration))
    name = StringField(unique=True, required=True)
