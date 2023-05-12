import argparse
import logging
import os
from abc import ABC, abstractmethod

import yaml
from corregivos.lang import memoized


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
        return yaml.safe_load(arg)

class CommandLine:

    def __init__(self):
        self.config={}
        self.arg_parser=argparse.ArgumentParser()


    def make(self):
        self._add_args()
        args = self.arg_parser.parse_args()
        return self._new(args)
    
    def _new(self, args):
        return self

    def _add_args(self):
        self.arg_parser.add_argument("--dir", action=Set, holder=self, type=Folder(create=True), help="Destination directory", default="~")
        self.arg_parser.add_argument("--config", action=Set, holder=self, type=FileOrValue(contentType=Yaml()), help="Name of config file. If is not a path then use `dir` directory", default="config.yaml")

    def __getattr__(self, name):
        value=None
        if name in self.__dict__:
            value = super().__getattr__(name)
        return value if value is not None else self.config.get(name)

