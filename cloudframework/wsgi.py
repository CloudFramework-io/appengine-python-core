from .core import core as core
import webapp2,os

class CoreWebApp2(webapp2.RequestHandler):
    def get(self): self.init('get')
    def put(self): self.init('put')
    def delete(self): self.init('delete')
    def post(self): self.init('post')
    def head(self): self.init('head')
    def options(self): self.init('options')
    def trace(self): self.init('trace')

    def init(self,method):
        core.init()
        core.dispatchWebApp2(method, self)

active_debug = os.environ.get('SERVER_SOFTWARE', '').startswith('Dev')
app = webapp2.WSGIApplication([(r'.*', CoreWebApp2)], debug=True)
# to start using it, run: core.init()
