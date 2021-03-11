# NOTICE
#
# This software was produced for the U. S. Government
# under Basic Contract No. W15P7T-13-C-A802, and is
# subject to the Rights in Noncommercial Computer Software
# and Noncommercial Computer Software Documentation
# Clause 252.227-7014 (FEB 2012)
#
# (C) 2017 The MITRE Corporation.

from mongoengine.fields import StringField, ListField, EmbeddedDocument, EmbeddedDocumentField, DateTimeField

from app.cascade.database import UniqueDocument


class IPLease(EmbeddedDocument):
    address = StringField()
    start_time = DateTimeField()
    end_time = DateTimeField()


class Host(UniqueDocument):
    fqdn = StringField()
    hostname = StringField()
    interfaces = ListField(StringField())
    leases = ListField(EmbeddedDocumentField(IPLease))
    users = ListField(StringField())

    def get_uuid_tuple(self):
        return self.hostname,
