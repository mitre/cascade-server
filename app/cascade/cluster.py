# NOTICE
#
# This software was produced for the U. S. Government
# under Basic Contract No. W15P7T-13-C-A802, and is
# subject to the Rights in Noncommercial Computer Software
# and Noncommercial Computer Software Documentation
# Clause 252.227-7014 (FEB 2012)
#
# (C) 2017 The MITRE Corporation.

import logging
from collections import defaultdict

from mongoengine.fields import EmbeddedDocumentField, StringField, DictField, ListField, BooleanField, IntField
from mongoengine.document import Document, EmbeddedDocument

from app.cascade.data_model.query import EmptyQuery, FieldQuery, QueryTerm


logger = logging.getLogger(__name__)


class ClusterKey(EmbeddedDocument):
    name = StringField()
    status = BooleanField(default=True)


class HierarchicalClusterNode(EmbeddedDocument):
    children = ListField(EmbeddedDocumentField('self'))
    size = IntField(default=0)
    key = StringField()
    value = StringField()
    leaf = BooleanField(default=False)

    def compare_event(self, event):
        status = (self.key is None) or (event.get(self.key, '').lower() == self.value.lower())
        status = status and (len(self.children) == 0 or any(node.compare_event(event) for node in self.children))
        return status

    def get_query(self):
        """
        :rtype QueryTerm
        """
        query = EmptyQuery
        if self.key is not None:
            query &= (FieldQuery(self.key) == self.value)

        if len(self.children):
            children_query = EmptyQuery
            for child in self.children:
                children_query |= child.get_query()
            query &= children_query
        return query

    def cluster_events(self, events, min_size=1, max_children=float("inf")):
        """
        :param List[dict] events: A list of key-value pairs to cluster on
        :param set skipped: A set of all of the clustered keys in the ancestry
        :param int min_size: Minimum cluster size
        :param float max_children: Maximum number of children before collapsing a cluster
        """
        total_clusters = 1
        num_children = 0

        if self.key is not None:
            events = [{k: v for k, v in event.items() if k != self.key} for event in events]

        self.size = sum(_.get('_size', 1) for _ in events)
        remaining_events = events

        while len(remaining_events) and num_children < max_children:
            best_key = None
            best_value = None
            best_count = 0

            counts = defaultdict(int)
            for event in remaining_events:
                for k, v in event.items():
                    # Use case insensitivity to cluster
                    lower_v = str(v).lower()
                    if k == self.key or k == '_size':
                        continue
                    size = event.get('_size', 1)
                    count = counts[k, lower_v] + size
                    counts[k, lower_v] = count
                    if count > best_count or (count == best_count and (k, v) <= (best_key, best_value)):
                        best_key, best_value, best_count = k, v, count

            # Cluster size must be greater than 1
            if best_count < min_size:
                self.leaf = True
                break

            lower_val = str(best_value).lower()
            biggest_cluster = [event for event in remaining_events if str(event.get(best_key, '')).lower() == lower_val]
            remaining_events = [event for event in remaining_events if str(event.get(best_key, '')).lower() != lower_val]

            # Add the new node to the cluster
            node = HierarchicalClusterNode(key=best_key, value=str(best_value))
            total_clusters += node.cluster_events(biggest_cluster, min_size=min_size, max_children=max_children)
            num_children += 1
            self.children.append(node)

        if num_children >= max_children:
            self.children = []
            self.leaf = True
        return total_clusters

    def used_keys(self):
        keys = set()
        if self.key:
            keys.add(self.key)
        return keys.union(*tuple(child.used_keys() for child in self.children))

    def recover_events(self):
        remaining = self.size
        # it's possible for the size of a node to be bigger than the size of all of its children
        for children in self.children:
            for cluster in children.recover_events():
                if self.key is not None:
                    cluster[self.key] = self.value
                remaining -= cluster['_size']
                yield cluster
        if remaining > 0 and self.key is not None:
            yield {self.key: self.value, '_size': remaining}


class HierarchicalCluster(Document):
    meta = {'abstract': True}
    root = EmbeddedDocumentField(HierarchicalClusterNode)
    original_root = EmbeddedDocumentField(HierarchicalClusterNode)
    keys = ListField(EmbeddedDocumentField(ClusterKey))

    def __init__(self, *args, **kwargs):
        super(HierarchicalCluster, self).__init__(*args, **kwargs)
        if self.root is None:
            self.root = HierarchicalClusterNode()

    def compare_event(self, event):
        """:param dict fields: The key:value pairs to be compared against the white list """
        return self.root.compare_event(event)

    def recover_events(self):
        return list(self.root.recover_events())

    def get_query(self):
        return self.root.get_query()

    def cluster_events(self, events, min_size=1, max_children=float("inf")):
        active_keys = {'_size'}
        active_keys.update(key.name for key in self.keys if key.status)

        # for each event, strip out the ignored keys
        events = [{k: v for k, v in _.items() if k in active_keys} for _ in events]

        # reset the root and update the clusters
        self.root = HierarchicalClusterNode()
        return self.root.cluster_events(events, min_size=min_size, max_children=max_children)

    def reset(self):
        self.root = self.original_root
        for key in self.keys:
            key.status = True

    def used_keys(self):
        return tuple(self.root.used_keys())
