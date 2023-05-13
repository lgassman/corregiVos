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

def Factory(arg):
    splited = arg.split(".")
    module_name=".".join(splited[:-1])
    class_name = splited[-1]
    module = importlib.import_module(module_name)
    class_ = getattr(module, class_name)
    return class_()
