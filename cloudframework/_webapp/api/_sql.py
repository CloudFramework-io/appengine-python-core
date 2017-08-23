from cloudframework.restful import RESTFul
from collections import OrderedDict

class API(RESTFul):

    def main(self):

        # loading sql class
        sql = self.core.loadClass('DataSQL')
        if sql == None: return self.setError('Error loading DataSQL',503,'system-error')


