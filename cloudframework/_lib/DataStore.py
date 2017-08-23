from google.appengine.ext import deferred
from google.appengine.ext import ndb
from collections import OrderedDict

class ndbClass(ndb.Expando):
    entity = None

    def init(self,entity):
        self.entity = entity


class DataStore:
    core = None
    spacename = None
    ndbModule = None
    schema = None


    def __init__(self,core):
        self.core = core
        self.spacename = core.system.spacename
        self.ndbModule = ndbClass()
        self.schema = None

    def init(self, entity_name, schema):
        self.ndbModule.init(entity_name)
        self.schema = schema
        for (key,value) in schema['model'].items():

            pass


