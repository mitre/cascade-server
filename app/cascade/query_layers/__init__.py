# NOTICE
#
# This software was produced for the U. S. Government
# under Basic Contract No. W15P7T-13-C-A802, and is
# subject to the Rights in Noncommercial Computer Software
# and Noncommercial Computer Software Documentation
# Clause 252.227-7014 (FEB 2012)
#
# (C) 2017 The MITRE Corporation.

from app.cascade.query_layers import base
from app.cascade.query_layers import splunk
from app.cascade.query_layers import elastic
from app.cascade.query_layers import mongo

from .base import DataModelQueryLayer, DatabaseInfo, CascadeQueryLayer, UserDatabaseInfo

platforms = (
    elastic.ElasticAbstraction,
    splunk.SplunkAbstraction,
    mongo.MongoAbstraction,
    DataModelQueryLayer,
    CascadeQueryLayer
)
mappings = {_.platform: _ for _ in platforms}
""":type: dict[str, DataModelQueryLayer] """
