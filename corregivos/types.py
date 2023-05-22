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

class FilePath:
    def __init__(self, parentFolder="."):
        self.parentFolder=parentFolder

    def __call__(self, arg):
        path = os.path.expanduser(arg)
        if os.path.isabs(path):
            return path
        else:
            folder = self.parentFolder() if callable(self.parentFolder) else self.parentFolder 
            return os.path.join(folder, path)

class FileOrValue():
    def __init__(self, parentFolder=".", contentType=str):
        self.contentType = contentType 
        self.parentFolder=parentFolder

    def __call__(self, arg):
        path = os.path.expanduser(arg)
        if not os.path.isfile(path):
            folder = self.parentFolder() if callable(self.parentFolder) else self.parentFolder 
            path=os.path.expanduser(os.path.join(folder, arg))
            if not os.path.isfile(path):
                return self.contentType(arg)
        with open(path, 'r') as f:
            content = f.read().strip()
            return self.contentType(content)

def Yaml(arg):
    if arg.endswith(".yaml"):
        return {} #default value was a inexistent path, transform to empty dict
    else:
        return yaml.safe_load(arg)

def Csv(arg):
    if arg.endswith(".csv"):
        return {} #default value was a inexistent path, transform to empty dict
    else:
        return [row for row in csv.DictReader(StringIO(arg))] #ufa, ya era un io antes, luego se hizo string y ahora lo necesito como io :(

class Factory:
    
    def __init__(self, context=None):
        self.context =context
    
    def __call__(self, arg):
        return self._get_value(arg)
    
    def _get_value(self, valueOrClassWithArgsOrContextkey, kwargs=None):
        if isinstance(valueOrClassWithArgsOrContextkey, str): 
            if valueOrClassWithArgsOrContextkey.startswith("$$") and self.context:
                valueOrClassWithArgsOrContextkey = valueOrClassWithArgsOrContextkey.replace("$", "", 1)
                return self._new_from_string(valueOrClassWithArgsOrContextkey, kwargs=kwargs)
            elif valueOrClassWithArgsOrContextkey.startswith("$") and self.context:
                valueOrClassWithArgsOrContextkey = valueOrClassWithArgsOrContextkey.replace("$", "", 1)
                return getattr(self.context, valueOrClassWithArgsOrContextkey)
            return self._new_from_string(valueOrClassWithArgsOrContextkey, kwargs=kwargs)
        elif isinstance(valueOrClassWithArgsOrContextkey, dict):
            x = [ self._get_value(key, valueOrClassWithArgsOrContextkey[key]) for key in valueOrClassWithArgsOrContextkey ]
            return x[0] if len(x) == 1 else x #Si no es 1 que es?
        elif isinstance(valueOrClassWithArgsOrContextkey, list):
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


