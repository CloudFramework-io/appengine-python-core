from cloudframework.core import core
from collections import OrderedDict
import json
import logging


is_array = lambda var: isinstance(var, (list, tuple))
is_string = lambda var: isinstance(var, (str, unicode))

class RESTFul():
    core = None
    returnData = None
    method = None
    wsgi_handler = None
    formParams = None
    params = None
    error = None
    errorMsg = None
    code = 'ok'
    status = 200
    contentTypeReturn = 'JSON'
    codeLib = None
    codeLibError = None

    def __init__(self):
        self.core = core
        self.method = None
        self.wsgi_handler = None
        self.formParams = OrderedDict()
        self.params = []
        self.error = False
        self.errorMsg = []
        self.code = 'ok'
        self.status = 200
        self.contentTypeReturn = 'JSON'
        self.codeLib = OrderedDict()
        self.codeLibError = OrderedDict()

        self.returnData = OrderedDict()
        self.returnData['success'] = True;
        self.returnData['status'] = 200;
        self.returnData['code'] = 'ok';
        self.returnData['url'] = self.core.system.url['host_url_uri']
        self.returnData['method'] = self.method
        self.returnData['ip'] = '127.0.0.1'

        # add basic error code
        self.addCodeLib('ok', 'OK', 200)
        self.addCodeLib('inserted', 'Inserted succesfully', 201)
        self.addCodeLib('no-content', 'No content', 204)
        self.addCodeLib('form-params-error', 'Wrong form paramaters', 400)
        self.addCodeLib('system-error', 'There is a problem in the platform', 503)
        self.addCodeLib('datastore-error', 'There is a problem with the DataStore', 503)
        self.addCodeLib('db-error', 'There is a problem in the DataBase', 503)
        self.addCodeLib('params-error', 'Wrong parameters', 400)
        self.addCodeLib('security-error', 'You don\'t have right credentials', 401)
        self.addCodeLib('not-allowed', 'You are not allowed', 403)
        self.addCodeLib('not-found', 'Not Found', 404)
        self.addCodeLib('method-error', 'Wrong method', 405)
        self.addCodeLib('conflict', 'There are conflicts', 409)
        self.addCodeLib('gone', 'The resource is not longer available', 410)
        self.addCodeLib('unsupported-media', 'Unsupported Media Type', 415)

    def init(self,method,handler):
        self.method = method;
        self.returnData['method'] = self.method
        self.wsgi_handler = handler

        # formParams
        for key in self.wsgi_handler.request.arguments():
            # potential JSON raw content
            if key[0] =='{':
                try:
                    _raw_json = json.loads(key,object_pairs_hook=OrderedDict)
                    for k,v in _raw_json.items():
                        self.formParams[k] = v
                except:
                    self.core.logs.add('Warning. RESTFul.formParams ERROR trying to decode _rawcontent_ '+key[:10]+"...")
                    pass
                #{reg_dict[k]: v for k, v in ord_dict.items()}
                pass
            else:
                self.formParams[key] = self.wsgi_handler.request.get(key)

        # params
        api_url = self.core.system.url['url'].replace(self.core.config.get('core_api_url'), '', 1)
        self.params = api_url.split('/')
        self.params.pop(0)
        self.params.pop(0)
        if len(self.params) > 0 and not(self.params[0]): self.params.pop(0)

    def addReturnData(self,value):
        if 'data' not in self.returnData.keys():
            self.setReturnData(value)
        else:
            if not is_array(self.returnData['data']):
                self.returnData['data'] = [self.returnData['data']]
            self.returnData['data'].append(value)

    def setReturnData(self, value):
        self.returnData['data'] = value

    def setError(self, error, status=400, code="params-error"):
        self.errorMsg = []
        self.addError(error,status,code)

    def addError(self,error,status=400,code='params-error'):
        self.errorMsg.append(error)
        self.error = True
        self.status = status
        self.code = code

    def addCodeLib(self,code, msg, error=400):
        self.codeLib[code] = msg
        self.codeLibError[code] = error

    def getCodeLib(self,code):
        if code in self.codeLib:
            return str(self.codeLib[code])
        else:
            return code

    def getCodeLibError(self,code):
        if code in self.codeLibError:
            return self.codeLibError[code]
        else:
            return 400

    def setErrorFromCodeLib(self,code,extramsg=''):
        if is_array(extramsg): extramsg = ": "+json.dumps(extramsg)
        self.addError("["+str(self.getCodeLibError(code))+": "+code+"] "+self.getCodeLib(code)+extramsg,self.getCodeLibError(code),code)
        pass

    def sendHeaders(self):
        """
        More info: https://en.wikipedia.org/wiki/List_of_HTTP_status_codes
        """
        if self.core.isThis.terminal(): return

        status_message = "HTTP/1.0 200 OK"
        if self.status == 201: status_message = "HTTP/1.0 201 Created"
        elif self.status == 204: status_message = "HTTP/1.0 204 No Content"
        elif self.status == 400: status_message = "HTTP/1.0 400 Bad Request"
        elif self.status == 401: status_message = "HTTP/1.0 401 Unauthorized"
        elif self.status == 403: status_message = "HTTP/1.0 403 Forbidden"
        elif self.status == 404: status_message = "HTTP/1.0 404 Not Found"
        elif self.status == 405: status_message = "HTTP/1.0 405 Method Not Allowed"
        elif self.status == 409: status_message = "HTTP/1.0 409 Conflict"
        elif self.status == 415: status_message = "HTTP/1.0 415 Unsupported Media Type"
        elif self.status == 503: status_message = "HTTP/1.0 503 Service Unavailable"
        else:
            if self.error: "HTTP/1.0 "+str(self.status)

        # defining content_type
        content_type = 'application/json'
        if self.contentTypeReturn =='TEXT': content_type = 'text/plain'
        elif self.contentTypeReturn =='HTML': content_type = 'text/html'

        self.wsgi_handler.response.status = self.status
        self.wsgi_handler.response.headers['Status'] = status_message
        self.wsgi_handler.response.headers['Content-Type'] = content_type

    def send(self):
        self.returnData['success'] = not(self.error)
        self.returnData['status'] = self.status
        self.returnData['code'] = self.code

        # add local errors and system errors
        if self.error :
            self.returnData['errors'] = self.errorMsg ;

        # add system-logs
        if self.core.logs.lines: self.returnData['system-logs'] = self.core.logs.data

        # add system-erros
        if self.core.errors.lines: self.returnData['system-errors'] = self.core.errors.data;

        # performance
        if '_p' in self.formParams.keys():
            self.returnData['_p'] = self.core._p.data;

        # sending output
        self.sendHeaders()
        self.wsgi_handler.response.write(json.dumps(self.returnData))


