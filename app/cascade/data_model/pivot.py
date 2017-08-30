# NOTICE
#
# This software was produced for the U. S. Government
# under Basic Contract No. W15P7T-13-C-A802, and is
# subject to the Rights in Noncommercial Computer Software
# and Noncommercial Computer Software Documentation
# Clause 252.227-7014 (FEB 2012)
#
# (C) 2017 The MITRE Corporation.

from .event import DataModelEvent, DataModelEventMeta, LabeledLink
from collections import defaultdict, namedtuple
import functools


PivotInfo = namedtuple('PivotInfo', ['name', 'func', 'reverse', 'depends', 'abstract', 'inverse',
                                     'source_class', 'source_actions', 'dest_class', 'dest_actions'])
forward_pivots = defaultdict(lambda: defaultdict(list))  # type: Dict[str, Dict[str, List[PivotInfo]]]
reverse_pivots = defaultdict(lambda: defaultdict(list))  # type: Dict[str, Dict[str, List[PivotInfo]]]
pivot_lookup = dict()


def register(src_cls, src_actions, dst_cls, dst_actions,
             reverse=False, depends=None, abstract=False, inverse=None, name=None):
    """
    :type src_cls: DataModelEvent | DataModelEventMeta
    :type src_actions: List[str]
    :type dst_cls: DataModelEvent | DataModelEventMeta
    :type dst_actions: List[str]
    :param reverse: Bool to represent the direction of the pivot
    :param inverse: String name of the inverse function (if reverse is True)
    :param List[str] depends: List of names of pivot dependencies
    :param bool abstract: True if the pivot is abstract and uses a black-box approach
    :param str name: Name of the pivot
    """

    depends = [] if depends is None else depends
    reverse = reverse or (inverse is not None)

    def decorator(f):
        pivot_name = f.__name__ if name is None else name

        @functools.wraps(f)
        def decorated(source_event, query_context):
            for pivot_event in f(source_event, query_context):
                source_label = LabeledLink(event=source_event, label=pivot_name)
                event_label = LabeledLink(event=pivot_event, label=pivot_name)

                if reverse is False:
                    pivot_event.update(add_to_set__reverse_links=source_event,
                                       add_to_set__labeled_reverse_links=source_label)
                    source_event.update(add_to_set__links=pivot_event,
                                        add_to_set__labeled_links=event_label)
                else:
                    pivot_event.update(add_to_set__links=source_event,
                                       add_to_set__labeled_links=source_label)
                    source_event.update(add_to_set__reverse_links=pivot_event,
                                        add_to_set__labeled_reverse_links=event_label)

                yield pivot_event

        pivot_info = PivotInfo(name=pivot_name, func=decorated, reverse=reverse, depends=depends, abstract=abstract,
                               inverse=inverse, source_class=src_cls, source_actions=src_actions,
                               dest_class=dst_cls, dest_actions=dst_actions)
        pivot_lookup[pivot_name] = pivot_info

        for action in src_actions:
            if reverse:
                reverse_pivots[src_cls][action].append(pivot_info)
            else:
                forward_pivots[src_cls][action].append(pivot_info)

        return f
    return decorator
