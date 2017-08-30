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
import bson.json_util
import datetime
from collections import defaultdict
from mongoengine.document import BaseDocument
from pymongo.errors import BulkWriteError
from mongoengine.queryset.base import BaseQuerySet
from pymongo.cursor import CursorType
from bson import ObjectId
import json
import cascade.database

default_collections = (
    'analytic',
    'attack_tactic',
    'attack_technique',
    'database_info',
    'session'
)


def all_collections(cascade_db):
    return list(cascade_db.collection_names())


def confirm(message):
    while True:
        answer = raw_input(message + " ").strip().lower()[:1]
        if answer == 'y':
            return True
        elif answer == 'n':
            return False


def json_default(obj):
    if isinstance(obj, BaseDocument):
        return obj.to_mongo().to_dict()
    elif isinstance(obj, BaseQuerySet):
        return list(obj._collection.find(obj._query, cursor_type=CursorType.EXHAUST))
    elif isinstance(obj, ObjectId):
        return str(obj)
    elif isinstance(obj, datetime.datetime):
        return obj.isoformat()
    else:
        raise TypeError('Object of type %s with value of %s is not JSON serializable' % (type(obj), repr(obj)))


def bson_default(obj):
    if isinstance(obj, BaseQuerySet):
        return json.loads(bson.json_util.dumps(list(obj._collection.find(obj._query, cursor_type=CursorType.EXHAUST))))
    elif isinstance(obj, BaseDocument):
        return json.loads(obj.to_json())
    else:
        raise TypeError('Object of type %s with value of %s is not JSON serializable' % (type(obj), repr(obj)))


def export_database(filename, collections=default_collections, select_all=False):
    database = cascade.database.pymongo()

    dump = []

    if select_all:
        collections = all_collections(database)
    elif not collections:
        collections = default_collections

    for c in collections:
        print("Dumping collection {}".format(c))
        dump.append({'collection': c, 'content': list(database[c].find())})

    with open(filename, 'w') as f:
        f.write(bson.json_util.dumps(dump, indent=2, sort_keys=True))


def import_database(dump, collections=None, overwrite=None):
    database = cascade.database.pymongo()

    if not isinstance(dump, list):
        raise ValueError("Dump file is not a BSON list")

    for partial_dump in dump:
        collection = partial_dump['collection']
        content = partial_dump['content']

        if collections is not None and collection not in collections:
            continue

        if len(content):
            print("Importing collection {}".format(collection))
            try:
                database[collection].insert_many(content)
            except BulkWriteError:
                replace = overwrite
                if replace is None:
                    replace = confirm("Matching documents exist in collection {}. Overwrite existing? [Y/N]".format(collection))
                for document in content:
                    doc_id = document.get('_id')

                    if doc_id is None:
                        database[collection].insert_one(document)
                    elif database[collection].find_one({'_id': doc_id}):
                        if replace:
                            database[collection].save(document)
                    else:
                        database[collection].insert_one(document)


def import_database_from_file(filename, collections=None, overwrite=None):
    with open(filename, 'r') as f:
        dump = bson.json_util.loads(f.read())

    import_database(dump, collections=collections, overwrite=overwrite)


def purge_database(collections=default_collections, select_all=False, prompt=True):
    database = cascade.database.pymongo()

    if select_all:
        collections = all_collections(database)
    elif not collections:
        collections = default_collections

    if not prompt or confirm("Are you sure you want to remove the following collections?\n{}\nY/N? ".format(", ".join(collections))):
        for collection in collections:
            print("Removing collection {}".format(collection))
            database[collection].drop()


def command_to_argv(command_line):
    arguments = []
    pending_arg = ''
    quoted = False
    last_char = None

    for i, char in enumerate(command_line):
        if quoted:
            if char == '\\':
                # delay processing because it could be used to escape something
                pass

            elif char == '"' and last_char == '\\':
                pending_arg += char

            elif char == '"':
                arguments.append(pending_arg)
                pending_arg = ''
                quoted = False

            else:
                if last_char == '\\':
                    pending_arg += last_char
                pending_arg += char

        elif char in (' ', '\t'):
            if len(pending_arg):
                arguments.append(pending_arg)
                pending_arg = ''

        elif not len(pending_arg) and char == '"':
            quoted = True

        else:
            pending_arg += char

        last_char = char

    if len(pending_arg):
        arguments.append(pending_arg)

    return arguments


def next_arg(args, flag, case=False):
    """
    :param list args: The list of command line arguments
    :param str flag: The list of command line arguments
    :param bool case: Pay attention to case sensitivity
    """
    lookup_args = args if case else [_.lower() for _ in args]
    flag = flag if case else flag.lower()

    if flag in lookup_args:
        index = lookup_args.index(flag)
        arg_index = index + 1
        if arg_index < len(args):
            return args[arg_index]


class AuthenticationError(Exception):
    pass
