import argparse
import logging
import os
from abc import ABC, abstractmethod

import yaml
import csv
from io import StringIO
import logging
import logging.config


class Set(argparse.Action):
    def __init__(self, option_strings, dest, holder, default=None, type=str, **kwargs):
        if not isinstance(type, SetType):
            type=DecoratorSetType(holder=holder, dest=dest, decorated=type)
        else:
            self._set_in_type(type,"holder", holder)
            self._set_in_type(type,"dest", dest)
        super().__init__(option_strings, dest, default=default, type=type, **kwargs)
        
    
    def _set_in_type(self, type, attr, value):
        if hasattr(type, attr) and not getattr(type, attr):
                setattr(type, attr, value)        
        
    def __call__(self, parser, namespace, values, option_string=None):
        setattr(namespace, self.dest, values)


class SetType:
    def __init__(self, holder=None, dest=None):
        self.holder=holder
        self.dest=dest
    
    def __call__(self, arg):
        value = self.transform(arg)
        setattr(self.holder, self.dest, value)
    
    def transform(self, arg):
        return arg

class DecoratorSetType(SetType):
    def __init__(self, holder, dest, decorated):
        super().__init__(holder, dest)
        self.decorated = decorated

    def transform(self, arg):
        return self.decorated(arg)
    


class Folder(SetType):
    def __init__(self, create=False, validate=True, **kwargs):
        super().__init__(**kwargs)
        self.create=create
        self.validate=validate

    def transform(self, arg):
        value=os.path.expanduser(arg)
        if not os.path.exists(value):
            if self.create:
                os.mkdir(value)
            elif self.validate:
                raise argparse.ArgumentTypeError(f"{value} is not a valid folder")
        return value

class FileOrValue(SetType):
    def __init__(self, parentFolder="dir", contentType=str, **kwargs):
        super().__init__(**kwargs)
        self.parentFolder = parentFolder
        self.contentType = contentType 

    def transform(self, arg):
        path = os.path.expanduser(arg)
        if not os.path.isfile(path):
            folder = getattr(self.holder, self.parentFolder) 
            path=os.path.expanduser(os.path.join(folder, arg))
            if not os.path.isfile(path):
                return self.contentType(arg)
        try:
            with open(path, 'r') as f:
                content = f.read().strip()
                return self.contentType(content)
        except:
            logging.exception("Que es esto!")
            raise

class Yaml:
    def __call__(self, arg):
        if arg.endswith(".yaml"):
            return {} #default value was a inexistent path, transform to empty dict
        else:
            return yaml.safe_load(arg)

def Csv(arg):
    if arg.endswith(".csv"):
        return {} #default value was a inexistent path, transform to empty dict
    else:
        return [row for row in csv.DictReader(StringIO(arg))] #ufa, ya era un io antes, luego se hizo string y ahora lo necesito como io :(

class CommandLine:

    def __init__(self):
        self.config={}
        self.arg_parser=argparse.ArgumentParser()


    def make(self):
        self._add_args()
        args = self.arg_parser.parse_args()
        if self.logging:
            logging.config.dictConfig(self.logging)
        return self._new(args)
    
    def _new(self, args):
        return self
    
    def add_argument(self, *args, **kwargs):
        if "action" not in kwargs:
            kwargs["action"] = Set
            kwargs["holder"] = self
        self.arg_parser.add_argument(*args, **kwargs)

    def _add_args(self):
        self.add_argument("--dir", type=Folder(create=True), help="Destination directory", default="~")
        self.add_argument("--config", type=FileOrValue(contentType=Yaml()), help="Name of config file. If is not a path then use `dir` directory", default="config.yaml")

    def __getattr__(self, name):
        if name in ["config", "arg_parser"]: 
            return None
        return self.config.get(name)

