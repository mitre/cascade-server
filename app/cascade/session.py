# NOTICE
#
# This software was produced for the U. S. Government
# under Basic Contract No. W15P7T-13-C-A802, and is
# subject to the Rights in Noncommercial Computer Software
# and Noncommercial Computer Software Documentation
# Clause 252.227-7014 (FEB 2012)
#
# (C) 2017 The MITRE Corporation.

from __future__ import print_function

import json
import logging

from gevent.queue import Queue
from mongoengine.document import Document, EmbeddedDocument
from mongoengine.fields import EmbeddedDocumentField, StringField, ReferenceField, ListField

from analytics import AnalyticResult, Analytic, AnalyticConfiguration
from .database import DateRange, DisjointSet
from query_layers import DataModelQueryLayer
from .data_model.event import DataModelEvent
from .. import async

logger = logging.getLogger(__name__)


class QueryContext(DataModelQueryLayer):
    def __init__(self, query_layer, time_range=None, session=None):
        """
        :param DataModelQueryLayer query_layer: The query layer (likely the user object)
        :param DateRange time_range: Time range if there is no session context
        :param Session session: The session object to be queried over
        """
        self.session = session
        self.query_layer = query_layer
        self._range = time_range

    def _get_range(self):
        """ :rtype: DateRange """
        if self.session is not None:
            return self.session.range
        else:
            return self._range

    def query(self, expression, baseline=False, **kwargs):
        new_args, expression = self._update_defaults(kwargs, expression)
        results = self.query_layer.query(expression, **new_args)
        return results

    def external_analytics(self):
        # this shouldn't make any sense
        raise NotImplementedError()

    def _update_defaults(self, kwargs, expression):
        new_args = kwargs.copy()
        time_range = self._get_range()

        new_args['start'], new_args['end'] = time_range.constrain(start=kwargs.get('start'), end=kwargs.get('end'))

        return new_args, expression


class SessionState(EmbeddedDocument):
    analytics = ListField(EmbeddedDocumentField(AnalyticConfiguration))


class SessionStream(object):
    __queues = {}

    def __init__(self, session):
        self.count = 0
        self.queues = {}
        self.session = session

    @classmethod
    def get_queue(cls, session):
        s_id = str(session.id)
        if str(session.id) not in cls.__queues:
            cls.__queues[s_id] = cls(session)
        return cls.__queues[s_id]

    def add(self, item):
        """ :type item: DataModelEvent """

        for q in self.queues.values():
            if isinstance(q, Queue):
                q.put(json.dumps(item))

    def stream(self):
        self.count += 1
        queue_id = self.count

        if not async.enabled:
            # print('WARNING! Stream functionality will not work without gevent')
            raise StopIteration()

        q = Queue()
        self.queues[self.count] = q

        try:
            # Return all ready events
            # yield 'stored', jsonify(self.session.events())
            # Return events as they are placed into the queues
            for item in q:
                yield item

        except GeneratorExit:
            self.queues.pop(queue_id)
            q.put(StopIteration)


class Session(Document):
    __sessions = {}
    domain = StringField()
    range = EmbeddedDocumentField(DateRange, required=True)
    name = StringField(required=True)
    state = EmbeddedDocumentField(SessionState)

    def __init__(self, *args, **kwargs):
        super(Session, self).__init__(*args, **kwargs)
        self._queue = None

    def query_context(self, user):
        return QueryContext(self, user)

    @property
    def queue(self):
        """:rtype SessionStream """
        if self._queue is None:
            self._queue = SessionStream.get_queue(self)
        return self._queue

    def get_clusters(self):
        events = list(DataModelEvent.objects(sessions=self).no_dereference())
        results = list(AnalyticResult.objects(session=self).no_dereference())
        event_keys = set(_.id for _ in events)

        def get_neighbors(node):
            neighbors = []
            if isinstance(node, AnalyticResult):
                neighbors.extend(event for event in node.events if event.id in event_keys)
            elif isinstance(node, DataModelEvent):
                # TODO: Error check to handle for events outside of current session
                neighbors.extend(event for event in node.links if event.id in event_keys)
                neighbors.extend(event for event in node.reverse_links if event.id in event_keys)
            return neighbors

        uptree = DisjointSet(events + results, get_neighbors)
        clusters = []
        for cluster in uptree.clusters():
            new_cluster = {'events': [], 'results': []}
            for item in cluster:
                if isinstance(item, AnalyticResult):
                    new_cluster['results'].append(item)
                elif isinstance(item, DataModelEvent):
                    new_cluster['events'].append(item)
            clusters.append(new_cluster)
        return clusters


