import os
import yaml
import csv
from io import StringIO
import argparse
import importlib
        
class Folder():
    def __init__(self, create=False, validate=True):
        self.create=create
        self.validate=validate

    def __call__(self, arg):
        value=os.path.expanduser(arg)
        if not os.path.exists(value):
            if self.create:
                os.mkdir(value)
            elif self.validate:
                raise argparse.ArgumentTypeError(f"{value} is not a valid folder")
        return value

class ContextAware:
    def __init__(self, context=None, context_key=None):
        self.context=context
        self.context_key=context_key

# Trata de buscarlo en el parent forlde, si no en el contexto, si no en el directorio actual
class PathAware(ContextAware):
    def __init__(self, context=None, context_key=None, parent_folder=None):
        super().__init__(context=context, context_key=context_key)
        self.parent_folder=parent_folder
    
    def _folder(self):
        if self.parent_folder:
            return self.parent_folder() if callable(self.parent_folder) else self.parent_folder
        elif self.context and self.context_key:
            option=getattr(self.context, self.context_key)
            return option if option else self._defaultParentFolder()
    
    def _defaultParentFolder(self):
        return "."

class FilePath(PathAware):

    def __call__(self, arg):
        path = os.path.expanduser(arg)
        if os.path.isabs(path):
            return path
        else:
            return os.path.join(self._folder(), path)

class FileOrValue(PathAware):
    def __init__(self,  *args, contentType=str, **keyargs):
        self.contentType = contentType 
        super().__init__(*args,**keyargs)

    def __call__(self, arg):
        path = os.path.expanduser(arg)
        if not os.path.isfile(path):
            path=os.path.expanduser(os.path.join(self._folder(), arg))
            if not os.path.isfile(path):
                return self.contentType(arg)
        with open(path, 'r') as f:
            content = f.read().strip()
            return self.contentType(content)

def Yaml(arg):
    if arg.endswith(".yaml"):
        return {} #default value was a invalid path, transform to empty dict
    else:
        return yaml.safe_load(arg)

def Csv(arg):
    if arg.endswith(".csv"):
        return {} #default value was a invalid path, transform to empty dict
    else:
        return [row for row in csv.DictReader(StringIO(arg))] #ufa, ya era un io antes, luego se hizo string y ahora lo necesito como io :(

class Factory:
    
    def __init__(self, context=None):
        self.context =context
    
    def __call__(self, arg):
        return self._get_value(arg)
    
    def _get_value(self, valueOrClassWithArgsOrContextkey, kwargs=None): #TODO: Es cierto que todas las llamadas recursivas tienen que pasar por acá? sospecho que los casos de dic y lista deberían tener métodos separados
        if isinstance(valueOrClassWithArgsOrContextkey, str): 
            if valueOrClassWithArgsOrContextkey.startswith("$$") and self.context: #Literal string starting with $
                valueOrClassWithArgsOrContextkey = valueOrClassWithArgsOrContextkey.replace("$", "", 1)
                return self._new_from_string(valueOrClassWithArgsOrContextkey, kwargs=kwargs)
            elif valueOrClassWithArgsOrContextkey.startswith("$") and self.context: #Is a key of context
                valueOrClassWithArgsOrContextkey = valueOrClassWithArgsOrContextkey.replace("$", "", 1)
                return getattr(self.context, valueOrClassWithArgsOrContextkey)
            return self._new_from_string(valueOrClassWithArgsOrContextkey, kwargs=kwargs) #Listeral string or a class with or without args
        elif isinstance(valueOrClassWithArgsOrContextkey, dict): #a dict with 1 value. key is a class, value i sa dict with params. TODO: Testear si tengo un caso de de una clase con solo un agumento key=value
            x = [ self._get_value(key, valueOrClassWithArgsOrContextkey[key]) for key in valueOrClassWithArgsOrContextkey ]
            return x[0] if len(x) == 1 else x 
        elif isinstance(valueOrClassWithArgsOrContextkey, list): #una lista de argumentos
            return [ self._get_value(key, {}) for key in valueOrClassWithArgsOrContextkey ]
        else:
            return valueOrClassWithArgsOrContextkey
    
    def _new_from_string(self, arg, kwargs=None):
        arg_splited = arg.split()
        kwargs=kwargs or {}
        try:
            return self._new_instance(arg_splited[0], arg_splited[1:],kwargs)
        except (ImportError, AttributeError, ValueError):
            if not kwargs:
                return arg #No era una class, era un value
            raise

    def _new_instance(self, clazz, args, kwargs):
        splited = clazz.split(".")
        module_name=".".join(splited[:-1])
        class_name = splited[-1]
        module = importlib.import_module(module_name)
        class_ = getattr(module, class_name)
        return class_(*[self._get_value(x) for x in args], **{k: self._get_value(v) for k,v in kwargs.items()})


