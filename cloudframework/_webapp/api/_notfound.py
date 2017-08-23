from cloudframework.restful import RESTFul
from collections import OrderedDict

class API(RESTFul):

    def main(self):

        self.setError('endpoint not found', 404,'not-found')
        # Prepare response
        ret = OrderedDict()
        ret['notfound'] = self.core.version

        # Add response to JSON
        self.addReturnData(ret)