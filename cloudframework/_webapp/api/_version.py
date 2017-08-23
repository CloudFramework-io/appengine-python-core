from cloudframework.restful import RESTFul
from collections import OrderedDict

class API(RESTFul):

    def main(self):

        # Prepare response
        ret = OrderedDict()
        ret['version'] = self.core.version
        ret['formParams'] = self.formParams
        ret['params'] = self.params

        # Add response to JSON
        self.addReturnData(ret)
