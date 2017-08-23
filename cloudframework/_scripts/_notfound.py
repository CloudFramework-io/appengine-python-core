from cloudframework.core import CoreScript

class Script(CoreScript):

    def main(self):
        self.sendTerminal(self.script+ 'not found or error')
