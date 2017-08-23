from cloudframework.restful import RESTFul

class API(RESTFul):

    def main(self):

        # Add response to JSON
        self.addReturnData(self.core.config.data)