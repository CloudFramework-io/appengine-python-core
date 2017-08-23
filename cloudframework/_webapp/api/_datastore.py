from cloudframework.restful import RESTFul
from collections import OrderedDict


class API(RESTFul):
    def main(self):
        # loading sql class
        ds = self.core.model.getDSObjectFromModel('SubscriptionHistory')
        if self.core.model.errorMsg: return self.setErrorFromCodeLib('system-error', self.core.model.errorMsg)

        self.addReturnData(ds.schema)
