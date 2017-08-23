# Copyright 2017 Cloudframework.io
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Use webapp2 to http requests and create WebApp2 class

import time
import os,sys
import json
import logging
import json
from collections import OrderedDict

is_array = lambda var: isinstance(var, (list, tuple, OrderedDict))
is_string = lambda var: isinstance(var, (str, unicode))


class Core():
    """
    """
    version = '1.1.0'
    _p = None          # CorePerformance
    session = None      # CoreSession
    system = None       # CoreSystem
    logs = None         # CoreLogs
    errors = None       # CoreLogs
    isThis = None       # CoreIs
    cache = None        # CoreCache

    security = None     # CoreSecurity
    user = None         # CoreUser
    config = None       # CoreConfig
    request = None      # CoreRequest
    localization = None # CoreLocalization
    model = None        # CoreModel

    wsgi_handler = None # webapp2.RequestHandler
    wsgi_method = None  # str: get, post, put etc..

    def init(self,root_path=''):
        self._p = CorePerformance()
        self.session = CoreSession()
        self.system = CoreSystem(root_path)
        self.logs = CoreLog()
        self.errors = CoreLog()
        self.isThis = CoreIs()
        self.cache = CoreCache()
        self._p.add('Construct Class with objects (__p,session[started=false],system,logs,errors,isThis,cache): Core.__init__' , __file__);

        self.security = CoreSecurity(self)
        self.user = CoreUser(self)
        self.config = CoreConfig(self,os.path.dirname(__file__)+'/config.json')
        self.request = CoreRequest(self)
        self.localization = CoreLocalization(self)
        self.model = CoreModel(self)
        self._p.add('Loaded security,user,config,request,localization,model objects with __session[started=false')


    def setAppPath(self,dir):
        if os.path.isdir(self.system.root_path+dir):
            self.system.app_path = self.system.root_path+dir
            self.system.app_url = dir
        else:
            self.errors.add(dir + " doesn't exist. The path has to begin with /")

    def loadClass(self,className):
        """
        :param className: str
        :return: mix
        """
        if className=='DataSQL':
            from cloudframework._lib.DataSQL import DataSQL
            return DataSQL(self)
        elif className=='DataStore':
            from cloudframework._lib.DataStore import DataStore
            return DataStore(self)
        elif className == 'Buckets':
            from cloudframework._lib.Buckets import Buckets
            return Buckets(self)
        else:
            self.errors.add( "Core.loadClass "+className+" does not exist")
            return None


    def dispatchWebApp2(self, method, handler):
        """Dispath a logic for API or for a WEB PAGE. if url match
        with core_api_url then ir will be treated as API
        :param method: str
        :param handler: webapp2.RequestHandler
        :return: null
        """
        # init performance trace
        self._p.add('Core.dispatchWebApp2', __file__, 'note')

        # Evaluate if the route is API path based on core_api_url
        if self.system.url['url'].find(self.config.get('core_api_url')) == 0:
            file = '_version'

            # If in the route is more than 'core_api_url', replace file
            api_url =  self.system.url['url'].replace(self.config.get('core_api_url'),'',1)
            api_parts = api_url.split('/')
            if len(api_parts)>1 and api_parts[1]:
                file = api_parts[1]

            # if it is an internal file
            if file[0] == '_':
                script = os.path.dirname(__file__)+"/_webapp/api/"+file+".py"
                logging.info(script)

                # if script does not exist include _notfound.py
                if not os.path.isfile(script): file='_notfound'

                # import module
                module = __import__("_webapp.api."+file, globals(), locals(), ['API'], -1)

                # create the api object
                api = module.API()

            # try to read from webapp
            else:
                script = os.path.dirname(os.path.dirname(__file__)) + "/webapp/api/" + file + ".py"

                # if script does not exist include _notfound.py
                if not os.path.isfile(script):
                    file = '_notfound'
                    module = __import__("_webapp.api." + file, globals(), locals(), ['API'], -1)
                else:
                    module = __import__("webapp.api." + file, globals(), locals(), ['API'], -1)

                # create the api object
                api = module.API()

            # init api object
            api.init(method.upper(), handler)

            # execute main
            api.main()

            # end performance trace

            # send the results
            api.send()

        # Evaluate if it is a logic file
        else:
            pass

        self._p.add('Core.dispatchWebApp2', '', 'ennote')




        return

    def dispatchTerminalApp(self,script_path):
        # add root_path in the paths to include modules
        sys.path.append(self.system.root_path)

        # look for the module
        script_module = script_path.replace("/",".").replace(".py","")
        try:
            module = __import__(script_module , globals(), locals(), ['Script'], -1)
            script = module.Script(self,script_path)

        except Exception as ins:
            module = __import__('_scripts._notfound', globals(), locals(), ['Script'], -1)
            self.errors.add(ins.message)
            script = module.Script(self, script_path)

        script.main()
        script.end()

"""CorePerformance require the memory_usage
"""
try:
    from google.appengine.api.runtime import memory_usage
except ImportError:
    class MemoryUsage():
        def current(self):
            return -1
    def memory_usage():
        return MemoryUsage()
class CorePerformance:
    """
    """
    data = None
    root_path = None
    def __init__(self):
        self.data = OrderedDict()
        self.data['initMicrotime'] = time.time()
        self.data['lastMicrotime'] = self.data['initMicrotime']
        self.data['initMemory'] = memory_usage().current()
        self.data['lastMemory'] = self.data['initMemory']
        self.data['lastIndex'] = 1
        self.data['info'] = []
        self.data['info'].append( "File :"+__file__.replace(os.path.dirname(os.path.dirname(__file__)),""))
        self.data['info'].append("Init Memory Usage: "+str(self.data['initMemory']))
        self.data['init'] = OrderedDict()
        self.root_path = os.path.dirname(os.path.dirname(__file__))

    # init to calculate time and memory spent passing a spacename and key
    def init(self,spacename,key):

        # <editor-fold desc="Init self.data['init'][spacename][key]['mem'],['time'],['ok']">
        if spacename not in self.data['init'].keys():
            self.data['init'][spacename] = {}
        self.data['init'][spacename][key] = {"mem":memory_usage().current(),"time":time.time(),"ok":True}
        # </editor-fold>

    # end a call after a init to calculate time and memory spent
    def end(self,spacename,key,ok=True,msg=''):

        # <editor-fold desc="Verify if a previous init exist. If not return False and self.data['init'][spacename][key]['error']">
        if spacename not in self.data['init'].keys():
            self.data['init'][spacename] = {key:{"error":"CorePerformance.end with no previous CorePerformance.init"}}
            return False

        if key not in self.data['init'][spacename]:
            self.data['init'][spacename][key] = {"error":"CorePerformance.end with no previous CorePerformance.init"}
            return False
        # </editor-fold>

        # <editor-fold desc="Verify if a previous init exist. If not return False and self.data['init'][spacename][key]['error']">
        self.data['init'][spacename][key] = {
            "mem": self.data['init'][spacename][key]['mem'] - memory_usage().current()
            , "time": time.time()-self.data['init'][spacename][key]['time']
            , "ok": ok }

        if not ok:
            self.data['init'][spacename][key]['notes'] =  msg
        # </editor-fold>

    # add a entry for performance
    def add(self,title,file='',type='all'):

        # Hidding full path (security)
        file = file.replace(os.path.dirname(os.path.dirname(__file__)),"")

        # Preparing the line to save
        line = ''
        if type == 'note':
            line += "["+type
        else:
            line += str(self.data['lastIndex'])+" ["

        if file.__len__():
            file = " ("+file+")"

        # Calculating memory
        _mem = memory_usage().current()  - self.data['lastMemory'];
        if type == 'all' or type=='endnote' or type=='memory':
            line+= str(round(_mem, 3))+' Mb';
            self.data['lastMemory'] = memory_usage().current()

        # Calculating memory
        _time = time.time() -self.data['lastMicrotime']
        if type == 'all' or type=='endnote' or type=='time':
            line+= ', '+str(round(_time, 3))+' secs';
            self.data['lastMicrotime'] = time.time()

        # Adding the title
        line += '] '+str(title)

        # Adding accum data

        if type!='note':
            line = "[ "+str(round(memory_usage().current(),3))+" Mb, "+str(round(time.time() -self.data['initMicrotime'],3))+" secs] / "+line+file

        if type=='endnote':
            line = "["+type+"] "+line

        self.data['info'].append(line)
        self.data['lastIndex']+=1


class CoreSession:
    """
    """
    def __init__(self):
        pass


class CoreSystem:
    """
    """
    root_path = None
    app_path = None
    app_url = None
    url = None
    spacename = None

    def __init__(self,root_path=''):
        if not root_path: root_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.root_path = root_path
        print os.path.abspath(__file__)
        self.app_path = self.root_path+'/_webapp'
        self.app_url = '/_webapp'
        self.spacename = 'cloudframework'

        self.url = OrderedDict()

        self.url['https'] = True if ('HTTPS' in os.environ.keys() and os.environ.get('HTTPS') == 'on') else False
        self.url['protocol'] = 'https' if self.url['https'] else 'http'
        self.url['host'] = 'terminal' if ('HTTP_HOST' not in os.environ.keys()) else os.environ.get('HTTP_HOST')
        self.url['url'] = '' if ('PATH_INFO' not in os.environ.keys()) else os.environ.get('PATH_INFO')
        self.url['params'] = '' if ('QUERY_STRING' not in os.environ.keys()) else os.environ.get('QUERY_STRING')
        self.url['url_uri'] = self.url['url']+"?"+self.url['params']

        self.url['host_base_url'] = '' if (self.url['host'] == 'terminal') else self.url['protocol']+"://"+self.url['host']
        self.url['host_url'] = self.url['host_base_url']+self.url['url']
        self.url['host_url_uri'] = self.url['host_url']+"?"+self.url['params']

        self.url['script_name'] = '' if ('SCRIPT_NAME' not in os.environ.keys()) else os.environ.get('SCRIPT_NAME')
        self.url['parts'] = self.url['url'].split('/')
        self.url['parts'].pop(0)

    def getUrl(self,key):
        if key in self.url:
            return self.url[key]
        else:
            return None

    '''
'''


class CoreLog:
    """
    """
    lines = 0
    data = None

    def __init__(self):
        self.lines = 0
        self.data =[]

    def set(self,value):
        self.data = [value]
        self.lines = 1

    def add(self,value):
        self.data.append(value)
        self.lines+=1


class CoreIs:
    """
    """
    def __init__(self):
        pass
    def development(self):
        return not(os.getenv('SERVER_SOFTWARE', '').startswith('Google App Engine/'))
    def production(self):
        return os.getenv('SERVER_SOFTWARE', '').startswith('Google App Engine/')
    def terminal(self):
        return not('REMOTE_ADDR' in os.environ)


class CoreCache:
    """
    """
    def __init__(self):
        pass


class CoreSecurity:
    """
    """
    core = None

    def __init__(self,core):
        self.core = core            # type: Core


class CoreUser():
    """
    """
    core = None

    def __init__(self, core):
        self.core = core            # type: Core
        pass

    def readConfigJSONFile(self, path):
        pass


class CoreConfig():
    """Class to control the application configuration
    """
    core = None
    data = None
    lang = None
    _configPaths = None

    def __init__(self, core,file=''):
        """Init the configuration
        """
        self.core = core            # type: Core
        self.data = OrderedDict()
        self.lang = 'en'
        self._configPaths = []

        # init system values
        self.set('core_system_url',core.system.url['url'])
        self.set('core_system_default_lang',self.lang)
        self.set('core_api_url','/p/api')
        self.set('core_model_default','/model.json')
        self.set('core_spacename','cloudframework')

        self.set('wapploca_api_url', 'https://wapploca.org/h/api/wapploca')
        self.set('wapploca_cache_expiration_time',3600)
        self.set('_webapp', self.core.system.app_url)
        self.set('webapp_menupath_rule', None)
        self.set('webapp_menupath_data', [])

        # read file of configuration
        if file:
            self.readConfigJSONFile(file)

        # process special tags
        if(self.get('core_default_lang')):
            self.lang = self.get('core_default_lang')

    # read a configJSON file and send it to processConfigData
    def readConfigJSONFile(self, file):
        # Control we are not reading the same file to avoid infinite loops
        if file in self._configPaths:
            self.core.logs.add("Recursive config file: " + file);
            return

        # try to read the file
        self._configPaths.append(file)
        try:
            # open the file and send it to json.load expecting a valid json
            with open(file) as data_file:
               data = json.load(data_file,object_pairs_hook=OrderedDict)
            # process the data
            self.processConfigData(data)
        except Exception as inst:
            self.core.errors.add('Error CoreConfig.readConfigJSONFile reading file: '+file)
            self.core.errors.add(inst.message)

    def processConfigData(self,data):
        """ process a dictionary of config orders assignin it to data
        """
        for (cond, vars) in data.items():
            # just a comment
            if cond =='--': continue

            # convert potential tags {{tag}} when it is a string
            if is_string(vars):
                vars = self.convertTags(vars)

            # Evaluate to include the condition
            include = False # if True then we will include
            tagcode = ''    # if !='' then it is a tagcode with a special meaning.

            # if there is a potential tagcode
            if ':' in cond:
                cond = self.convertTags(cond.strip())
                (tagcode,tagvalue)  = cond.split(':',2)
                tagcode = tagcode.strip()
                tagvalue = tagvalue.strip()

                if self.isConditionalTag(tagcode):
                    # depends of the contion the info will be include in config
                    include = self.getConditionalTagResult(tagcode,tagvalue)
                
                elif self.isAssignationTag(tagcode):
                    # execute a command
                    self.setAssignationTag(tagcode, tagvalue, vars)
                
                else:
                    # unknown tagcode
                    self.core.errors.add('unknown tag: |' +tagcode + '|')
                    continue
            # it is just a key=>value
            else:
                include = True
                vars = {cond:vars}  # convert vars into a dict

            # continue if we do not have to include in CoreConfig.data
            if not include: continue

            # add in CoreConfig.data or call recursively processConfigData for potential tagcodes
            for (key, value) in vars.items():
                # it is a comment
                if key ==' --':continue

                # it is a potential tagcode
                if ':' in key:
                    self.processConfigData({key:value})
                # it is a key=>value
                else:
                    self.set(key,value)

    def convertTags(self, data):
        """ convert potential tags {{tag}}
        """

        # if not string the convert to string
        dumped = False
        if not(is_string(data)):
            data = json.dumps(data)
            dumped = True

        # Apply transformations
        if '{{rootPath}}' in data:  data = data.replace('{{rootPath}}',self.core.system.root_path)
        # TODO: apply transaformation
        # appPath
        # lang
        # confVar

        # reconvert to original
        if dumped:
            data = json.loads(data, object_pairs_hook=OrderedDict)


        # return transformed data
        return data

    def isConditionalTag(self,tag):
        """return true if the tag is conditional array"""
        return tag.lower() in ["uservar", "authvar", "confvar", "sessionvar", "servervar", "auth", "noauth", "development", "production"
                , "indomain", "domain", "interminal", "url", "noturl", "inurl", "notinurl", "beginurl", "notbeginurl"
                , "inmenupath", "notinmenupath", "isversion", "false", "true"]

    def getConditionalTagResult(self,tagcode, tagvalue):
        """return True or False based in a tagcode and tagvalue
        """
        ret = False # False by defautl

        # tags to evaluate
        evaluateTags = []

        # does tagvalue multples tagcodes '|', then add pairs tagcode: single value for or conditions
        while '|' in tagvalue:
            (tagvalue,tags) = tagvalue.split('|',2)
            evaluateTags.append([tagcode.strip().lower(),tagvalue.strip()])
            (tagcode,tagvalue) = tags.split(':',2)

        # add the last tagcode,tagvalue
        evaluateTags.append([tagcode.strip().lower(), tagvalue.strip()])

        # start evaluating tags
        for evaluateTag in evaluateTags:
            tagcode = evaluateTag[0].strip()
            tagvalue = evaluateTag[1].strip()
            if tagcode == 'uservar' or tagcode == 'authvar':
                pass
            elif tagcode =='confvar':
                pass
            elif tagcode =='true':
                ret = True
            elif tagcode =='false':
                pass
            elif tagcode =='interminal':
                ret = self.core.isThis.terminal();
            elif tagcode == 'indomain' or tagcode== 'domain':
                if 'HTTP_HOST' in os.environ:
                    HTTP_HOST = os.environ['HTTP_HOST']
                    domains = tagvalue.split(',')
                    for domain in domains:
                        pass
            elif tagcode =='production':
                ret = self.core.isThis.production()
            elif tagcode =='development':
                ret = self.core.isThis.development()
            else:
                self.core.errors.add('unknown tag: |'+ tagcode+ '|')
            if ret: break

        # return ret
        return ret

    def isAssignationTag(self,tag):
        """return true if the tag is assignation tag array"""
        return tag.lower() in ["webapp", "set", "include", "redirect", "menu","coreversion"]

    def setAssignationTag(self,tagcode, tagvalue, vars):
        # type: (object, object, object) -> object
        tagcode = tagcode.strip().lower()
        if tagcode == 'webapp':
            self.set(tagcode,vars)
            self.core.setAppPath(vars)
        elif tagcode == 'set': self.set(tagvalue, vars)
        elif tagcode == 'include':
            self.readConfigJSONFile(vars)
            pass
        elif tagcode == 'redirect': pass
        elif tagcode == 'menu':
            # The menu is only available for WSGI app
            if not self.core.isThis.terminal():
                # menu has to be an array of elements in vars
                if not(is_array(vars)):
                    self.core.errors.add("menu: tag does not contain an array")
                else:
                    vars = self.convertTags(vars) # convert potencial tags
                    for value in vars:
                        # verify the structure is right
                        if not(is_array(value)) or 'path' not in value.keys():
                            self.core.errors.add("menu: element does not contains an array with the path element")
                            print type(value) is OrderedDict
                        # add the line in pushMenu
                        else:
                            self.pushMenu(value)
                            pass
        elif tagcode == 'coreversion': pass
        else: self.core.errors.add('unknown tag: |' + tagcode + '|')

    def pushMenu(self, line):
        if 'webapp_menupath_rule' in self.data.keys() and self.data['webapp_menupath_rule']:
            # when menu path is set is because a previous menu has been found
            return

        if not (is_array(line)) or 'path' not in line.keys():
            self.core.logs.add('Missing path in menu line')
            self.core.logs.add(line)
        else:
            _found = False
            if '{*}' in line['path']:
                _found = self.core.system.url['url'].find(line['path'].replace('{*}','')) == 0
            else:
                _found = self.core.system.url['url'] == line['path'];

            # if _found we set all the vars as a config vars
            if _found:
                self.set('webapp_menupath_data', line)
                self.set('webapp_menupath_rule', line['path'])
                for (key,value) in line.items():
                    if 'path' == key: continue
                    value = self.convertTags(value)
                    self.set(key,value)

    def get(self,key):
        """get a key from data"""
        if(key in self.data):
            return self.data[key]
        else:
            return None

    def set(self,key,value):
        """set a key into data"""
        self.data[key] = value


class CoreRequest():
    """
    """
    core = None

    def __init__(self, core):
        self.core = core    # type: Core


class CoreLocalization():
    """
    """
    core = None

    def __init__(self, core):
        self.core = core    # type: Core


class CoreModel():
    """
    """
    core = None
    error = None
    errorMsg = None
    models = None
    models_readed = None

    def __init__(self, core):
        self.core = core        # type: Core
        self.error = False
        self.errorMsg = []
        self.models = OrderedDict()
        self.models_readed = False

    def readModels(self,path=''):

        # indicate that the method has been read at least once.
        self.models_readed

        # control potential names
        if not path: path = core.config.get('core_model_default')
        if not path: path = '/model.json'

        # create the complete path
        json_file_path = self.core.system.root_path+path


        # open the file and send it to json.load expecting a valid json
        try:
            with open(json_file_path) as data_file:
                data = json.load(data_file,object_pairs_hook=OrderedDict)
                if 'DataBaseTables' in data:
                    for model,value in data['DataBaseTables'].items():
                        self.models['db:'+model] = {'type':'db','data':value}

                if 'DataStoreEntities' in data:
                    for model, value in data['DataStoreEntities'].items():
                        self.models['ds:' + model] = {'type': 'ds', 'data': value}
        except Exception as inst:
            self.addError('Error CoreModel.readModels having problems reading %s json file: ' % path)
            self.core.errors.add(inst.message)
        return

    def getDBObjectFromModel(self,model):
        # check we have readed models
        if not self.models_readed: self.readModels()
        if self.error: return

        # check if model exist
        if "db:"+model not in self.models:
            return self.addError("CoreModel.getDBObjectFromModel %s not found" % model)

        # return the object
        db = self.core.loadClass('DataSQL')
        return db

    def getDSObjectFromModel(self, model_name):
        # check we have readed models
        if not self.models_readed: self.readModels()
        if self.error: return

        # check if model exist
        if "ds:"+model_name not in self.models:
            return self.addError("CoreModel.getDBObjectFromModel %s not found" % model_name)

        # return the object
        ds = self.core.loadClass('DataStore')
        ds.init(model_name, self.models["ds:" + model_name]['data'])
        return ds

    def setError(self, error):
        self.errorMsg = []
        self.addError(error)

    def addError(self,error):
        self.errorMsg.append(error)
        self.error = True


class CoreScript:
    core = None
    script = None
    error = None
    errorMsg = None
    def __init__(self,core,script):
        self.core = core    # type: Core
        self.script = script
        self.error = False
        self.errorMsg = []

        os.system('cls' if os.name == 'nt' else 'clear')
        print "init script: "+script
        print "--------"

    def sendTerminal(self,msg):
        print msg

    def end(self):
        print "\n\n"
        print "--------"
        print "ended script: "+self.script
        if self.error:
            print "ERRORS:"
            self.sendTerminal(self.errorMsg)
            print "\n\n"
        if self.core.errors.lines:
            print "SYSTEM-ERRORS:"
            self.sendTerminal(self.core.errors.data)
            print "\n\n"

    def setError(self, error):
        self.errorMsg = []
        self.addError(error)

    def addError(self, error):
        self.errorMsg.append(error)
        self.error = True




# Create the object core
core = Core();

