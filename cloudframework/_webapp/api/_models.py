from cloudframework.restful import RESTFul
from collections import OrderedDict

class API(RESTFul):

    def main(self):

        # loading sql class
        self.core.model.readModels() # read model /models.json
        if self.core.model.error: return self.setErrorFromCodeLib('system-error',self.core.model.errorMsg)

        # show the models in the project
        self.addReturnData(self.core.model.models.keys())


