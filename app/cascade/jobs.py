# NOTICE
#
# This software was produced for the U. S. Government
# under Basic Contract No. W15P7T-13-C-A802, and is
# subject to the Rights in Noncommercial Computer Software
# and Noncommercial Computer Software Documentation
# Clause 252.227-7014 (FEB 2012)
#
# (C) 2017 The MITRE Corporation.

from collections import defaultdict
from database import UniqueDocument, DateRange
from mongoengine.fields import StringField, ReferenceField, DictField, BooleanField, ListField, EmbeddedDocumentField, DateTimeField, IntField
from pymongo.errors import DocumentTooLarge
from session import Session, SessionStream, QueryContext
from analytics import AnalyticResult, Analytic, CascadeAnalytic, AnalyticConfiguration, AnalyticBaseline
from cluster import ClusterKey
from query_layers.mongo import MongoAbstraction
from data_model.event import event_lookup, DataModelEvent, DataModelQuery
from data_model.pivot import forward_pivots, reverse_pivots, pivot_lookup
from data_model.query import FieldQuery, EmptyQuery
from data_model.parser import lift_query
from .. import async
import logging
import datetime


# Job Types
logger = logging.getLogger(__name__)
mongo_query_layer = MongoAbstraction()


class Job(UniqueDocument):
    meta = {'allow_inheritance': True}
    CREATED = 'created'
    READY = 'ready'
    DISPATCHED = 'dispatched'
    STARTED = 'started'
    SUCCESS = 'success'
    FAILURE = 'failure'

    codes = [CREATED, READY, DISPATCHED, SUCCESS, FAILURE, STARTED]

    results = ListField(DictField())
    events = ListField(ReferenceField(DataModelEvent))
    count = IntField()
    user = ReferenceField('User')
    status = StringField(default=CREATED, choices=codes)
    message = StringField()
    uuid = StringField()
    created = DateTimeField(default=datetime.datetime.utcnow)
    started = DateTimeField(default=datetime.datetime.utcnow)
    updated = DateTimeField(default=datetime.datetime.utcnow)

    def touch(self):
        self.update(updated=datetime.datetime.utcnow())

    def update_start(self):
        self.update(started=datetime.datetime.utcnow())

    def run(self):
        raise NotImplementedError

    def __repr__(self):
        return "{}(uuid={})".format(type(self).__name__, repr(self.uuid))

    def get_query_context(self):
        user = self.user.login()
        if len(user.layers) == 0:
            raise ValueError("No query layers are defined for user, unable to run job")
        return QueryContext(user, session=self.session)

    def submit(self):
        self.update(status=Job.READY, message=None)

    def stream(self):
        pass

    def update(self, **kwargs):
        kwargs['updated'] = datetime.datetime.utcnow()
        return super(Job, self).update(**kwargs)

    def modify(self, query=None, **update):
        update['updated'] = datetime.datetime.utcnow()
        return super(Job, self).modify(**update)

    def save(self, *args, **kwargs):
        self.updated = datetime.datetime.utcnow()
        return super(Job, self).save(*args, **kwargs)

    @classmethod
    def add_to_session(cls, session, event):
        event.update(add_to_set__sessions=session.id)


class TuningJob(Job):
    analytic = ReferenceField(Analytic)
    range = EmbeddedDocumentField(DateRange)

    def get_uuid_tuple(self):
        return (self.analytic.id, self.user.id) + self.range.get_uuid_tuple()

    def get_query_context(self):
        return QueryContext(self.user.login(), time_range=self.range)

    def run(self):
        self.update_start()
        query_context = self.get_query_context()
        logger.debug('Training on {} with ctx {}'.format(self.analytic, query_context))
        baseline = AnalyticBaseline.objects(analytic=self.analytic).first()
        if baseline is None:
            baseline = AnalyticBaseline(analytic=self.analytic)

        baseline.time_range = self.range
        results = []
        found_keys = set()

        for i, output in enumerate(query_context.query(self.analytic)):
            fields = output['state']
            found_keys.update(fields.keys())
            results.append(fields)
            if i < 512:
                self.update(add_to_set__results=output, inc__count=1)
            else:
                self.update(inc__count=1)

        baseline.keys = [ClusterKey(name=k, status=True) for k in found_keys]
        baseline.cluster_events(results, min_size=1)
        baseline.original_root = baseline.root

        min_size = 1
        max_children = 1024

        # Continue to build a baseline until it works
        while max_children > 0:
            try:
                baseline.save()
                return
            except DocumentTooLarge:
                # try to dynamically adjust this until it fits
                baseline.cluster_events(results, min_size=min_size, max_children=max_children)
                baseline.original_root = baseline.root
                baseline.save()
                min_size += 1
                max_children = int(max_children * 0.9)

        # probably redundant, but useful to re-raise errors if the baseline isn't successful yet
        baseline.save()


class PivotJob(Job):
    session = ReferenceField(Session)
    event = ReferenceField(DataModelEvent)
    dependencies = ListField(ReferenceField('self'))
    reverse = BooleanField()
    pivot = StringField()

    @property
    def pivot_function(self):
        return pivot_lookup[self.pivot].func

    def get_uuid_tuple(self):
        return self.event.id, self.pivot, self.session.id, self.reverse

    def self_pivot(self, event, mode):
        return self.schedule_pivots(event, self.user, self.session, mode=mode)

    @classmethod
    def schedule_pivots(cls, event, user, session, mode='both'):
        event = event
        dependencies = defaultdict(list)
        job_lookup = {}
        count = 0

        if mode == 'forward':
            pivots = forward_pivots[type(event)][event.action]
        elif mode == 'reverse':
            pivots = reverse_pivots[type(event)][event.action]
        else:
            pivots = forward_pivots[type(event)][event.action] + reverse_pivots[type(event)][event.action]

        for pivot_info in pivots:
            job = PivotJob.update_existing(event=event, session=session, user=user, pivot=pivot_info.name, reverse=pivot_info.reverse)
            job_lookup[pivot_info.name] = job

            if job.status not in (Job.FAILURE, Job.CREATED):
                continue

            for dependency in pivot_info.depends:
                dependencies[pivot_info.name].append(dependency)

        for dependent in dependencies:
            dependent_job = job_lookup[dependent]
            for dependency in dependencies[dependent]:
                dependency_job = job_lookup[dependency]
                dependent_job.update(add_to_set__dependencies=dependency_job)

        # submit all the jobs (mark them as ready)
        for job in job_lookup.values():
            if job.status in (Job.CREATED, Job.FAILURE):
                job.submit()
                count += 1
        return count

    def run(self):
        self.update_start()
        query_context = self.get_query_context()
        dependencies = list(self.dependencies)

        def waiting():
            for dependency in dependencies:
                if dependency.status == Job.FAILURE:
                    raise RuntimeError("Job dependency failed.")
                if dependency.status != Job.SUCCESS:
                    dependency.reload()
                    return True
            return False

        while waiting():
            async.sleep(1)

        for pivot_event in self.pivot_function(self.event, query_context):
            self.update(add_to_set__events=pivot_event, inc__count=1)
            self.self_pivot(pivot_event, 'reverse' if self.reverse else 'forward')
            self.add_to_session(self.session, pivot_event)


class InvestigateJob(Job):
    session = ReferenceField(Session)
    event = ReferenceField(DataModelEvent)

    def get_uuid_tuple(self):
        return self.session.id, self.event.id, self.user.id

    def run(self):
        self.update_start()
        count = PivotJob.schedule_pivots(self.event, self.user, self.session, mode='both')
        self.update(count=count)


class ExtractEventsJob(Job):
    session = ReferenceField(Session)
    event_query = EmbeddedDocumentField(DataModelQuery)
    analytic_result = ReferenceField(AnalyticResult)
    analytic = ReferenceField(Analytic)
    mode = StringField(default=Analytic.FIRST_PASS, choices=Analytic.modes)

    def __init__(self, *args, **values):
        super(ExtractEventsJob, self).__init__(*args, **values)

        if self.session is None:
            self.session = self.analytic_result.session
        if self.analytic is None:
            self.analytic = self.analytic_result.analytic
        if self.uuid is None:
            self.uuid = self.get_uuid()

    def get_uuid_tuple(self):
        return self.analytic_result.id, hash(lift_query(self.event_query))

    def run(self):
        self.update_start()
        query_context = self.get_query_context()

        event_class = self.event_query.object
        event_action = self.event_query.action

        for result in query_context.query(self.event_query):
            event = event_class.update_existing(action=event_action, **result)
            self.update(add_to_set__events=event, inc__count=1)
            self.analytic_result.update(add_to_set__events=event)
            if self.mode in (Analytic.FIRST_PASS, Analytic.SECOND_PASS):
                investigate_job = InvestigateJob.update_existing(event=event, session=self.session, user=self.user)
                investigate_job.submit()


class CustomQueryJob(Job):
    mode = StringField(default=Analytic.FIRST_PASS, choices=Analytic.modes)
    session = ReferenceField(Session)
    events = ListField(ReferenceField(DataModelEvent))
    event_query = EmbeddedDocumentField(DataModelQuery)

    def get_uuid_tuple(self):
        return hash(lift_query(self.event_query)), self.mode, self.session.id

    def get_query_context(self):
        if self.mode == Analytic.SECOND_PASS:
            return QueryContext(mongo_query_layer, session=self.session)
        else:
            return super(CustomQueryJob, self).get_query_context()

    def run(self):
        self.update_start()
        query_context = self.get_query_context()

        event_class = self.event_query.object
        event_action = self.event_query.action

        for result in query_context.query(self.event_query):
            event = event_class.update_existing(action=event_action, **result)
            self.update(add_to_set__events=event, inc__count=1)
            self.add_to_session(self.session, event)

            if self.mode in (Analytic.FIRST_PASS, Analytic.SECOND_PASS):
                investigate_job = InvestigateJob.update_existing(event=event, session=self.session, user=self.user)
                investigate_job.submit()
            # TODO: Add special analytic result for custom queries
            # this would also help with ATT&CK labels
            # self.analytic_result.update(add_to_set__events=event)


class AnalyticJob(Job):
    session = ReferenceField(Session)
    analytic = ReferenceField(Analytic)
    mode = StringField(default=Analytic.FIRST_PASS, choices=Analytic.modes)

    def get_uuid_tuple(self):
        return self.analytic.id, self.session.id, self.mode, self.user.id

    def get_query_context(self):
        if self.mode == Analytic.SECOND_PASS:
            return QueryContext(mongo_query_layer, session=self.session)
        else:
            return super(AnalyticJob, self).get_query_context()

    def run(self):
        self.update_start()
        query_context = self.get_query_context()
        session = self.session
        analytic = self.analytic

        baseline = analytic.baseline
        baseline_query = None
        if baseline is not None:
            baseline_query = baseline.get_query()

        session.update(add_to_set__state__analytics=AnalyticConfiguration(analytic=analytic, mode=self.mode))

        query = analytic
        if isinstance(analytic, CascadeAnalytic) and baseline_query is not None:
            if baseline_query != EmptyQuery and self.mode != Analytic.IDENTIFY_ONLY_NO_BASELINE:
                query &= ~baseline_query

        if self.mode == Analytic.SECOND_PASS and isinstance(analytic, CascadeAnalytic):
            query = analytic

        output = query_context.query(query, session=session)

        for i, result in enumerate(output):
            # Don't break mongo if there are too many results
            if i < 5000:
                self.update(add_to_set__results=result)

            self.update(inc__count=1)

            # If the event is part of the baseline, then it can be skipped
            if self.mode in (Analytic.FIRST_PASS, Analytic.IDENTIFY_ONLY) and baseline and baseline_query.compare(result['state']):
                continue

            extracted_events = list(analytic.extract_events(result))
            if not len(extracted_events):
                continue

            # CascadeAnalytic will return events directly, which will be added directly to an analytic result
            if isinstance(extracted_events[0], DataModelEvent):
                AnalyticResult.update_existing(analytic=analytic, session=session, events=extracted_events)

                for event in extracted_events:
                    self.update(add_to_set__events=event)
                    self.add_to_session(session, event)

                    if self.mode in (Analytic.FIRST_PASS, Analytic.SECOND_PASS):
                        InvestigateJob.update_existing(event=event, session=self.session, user=self.user).submit()

            # Otherwise, a query needs to be performed, and the analytic result will be created before.
            # In this case, the UUID actually will be based off of the event mapping of the results
            elif isinstance(extracted_events[0], DataModelQuery):
                analytic_result = AnalyticResult.update_existing(analytic=analytic, session=self.session, result=result)
                for query in extracted_events:
                    job = ExtractEventsJob.update_existing(user=self.user,
                                                           query=query,
                                                           analytic_result=analytic_result,
                                                           session=session,
                                                           mode=self.mode)
                    """:type: ExtractedObjectJob """
                    # re-run the existing job if it needs to be
                    if job.status not in (Job.SUCCESS, Job.STARTED, Job.DISPATCHED):
                        job.submit()

            else:
                logger.warning("Unknown analytic. Unable to extract results")
