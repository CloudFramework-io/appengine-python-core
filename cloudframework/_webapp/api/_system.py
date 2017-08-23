from cloudframework.restful import RESTFul
from collections import OrderedDict

class API(RESTFul):

    def main(self):

        # Prepare response
        ret = OrderedDict()
        ret['root_path'] = self.core.system.root_path
        ret['app_path'] = self.core.system.app_path
        ret['app_url'] = self.core.system.app_url

        # Add response to JSON
        self.addReturnData(ret)
