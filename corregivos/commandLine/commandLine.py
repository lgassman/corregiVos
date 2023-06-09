import argparse
import logging
import logging.config
from corregivos.types import FileOrValue, Yaml, Folder, PathAware
from collections.abc import Iterable

# search in params first
# after that search in config file
# finally use default
# if default is callable call functions


class CommandLine:

    def __init__(self):
        self._values={}
        self._arg_parser=argparse.ArgumentParser()
        #self._config={}
        self._args=None
        self._defaults={}
        self._types={}

    def make(self):
        self.declare_params()
        self._args = self._arg_parser.parse_args()
        if self.logging:
            logging.config.dictConfig(self.logging)
        self._additional_validations()
        return self._new()
    
    def _additional_validations(self):
        pass
    
    def _new(self):
        return self
    
    def add_argument(self, *args, **kwargs):
        name = kwargs.get("dest")
        if not name:
            name = next(filter( lambda x : x.startswith("--") , args))[2:]
        if "default" in kwargs:
            self._defaults[name] = kwargs.get("default",None)
            del kwargs["default"]
        if "type" in kwargs:
            _type=kwargs.get("type")
            self._types[name]=_type
            del kwargs["type"]
            if isinstance(_type, PathAware):
                if not _type.context:
                    _type.context=self
                if not _type.context_key:
                    _type.context_key="dir"
        self._arg_parser.add_argument(*args, **kwargs)
    
    def add_config(self, name, type=None, default=None):
        if default is not None:
            self._defaults[name] = default
        if type is not None:
            self._types[name] = type

    def declare_params (self):
        self.add_argument("--dir", type=Folder(create=True), help="Destination directory", default="~")
        self.add_argument("--config", type=FileOrValue(contentType=Yaml), help="Name of config file. If is not a path then use `dir` directory", default="config.yaml")
    
    def directory(self):
        return self.dir
    
    def __getattr__(self, name):
        if name not in self._values:
            value = self.find_attr(name)
            self._values[name]=value
            return value
        else:
            return self._values.get(name)

    def _convert_by_type(self, name, value):
        if name in self._types:
            if isinstance(value, list):
                return [self._types[name](x) for x in value ]
            else:
                return self._types[name](value)
        else:
            return value

    def find_attr(self, name):
        if hasattr(self._args, name):
            value=getattr(self._args,name)
            if value is not None:
                return self._convert_by_type(name, value)
        value=None
        if name != "config":
            value = self.config and self.config.get(name)
        if value is None:
            value = self._defaults.get(name)
            if callable(value):
                value = value()
        self._convert_by_type(name, value)
        
        if name in self._types:
            if isinstance(value, list):
                return [self._types[name](x) for x in value ]
            else:
                return self._types[name](value)
        else:
            return value

