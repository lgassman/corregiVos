from functools import wraps
import subprocess 
import logging


def exec(cmd, check=True):
    _exec_logger().debug(cmd)
    try:
        result = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True, check=check)
        _log(result)
        return result
    except subprocess.CalledProcessError as error:
        _log(error)
        raise
def _exec_logger():
    return logging.getLogger("exec")

def _log(resultOrError):
        if(resultOrError.stdout):
            _exec_logger().debug(resultOrError.stdout)
        if(resultOrError.stderr):
            _exec_logger().error(resultOrError.stderr)


#Es una idea que no terminó de convencerme pero no la quiero borrar aun
class Mixable():

    @classmethod
    def mix(cls: type, mixins, attr=None):
        """
            base: if True cls is the base clase else clas is the super class
        """
        if isinstance(mixins, type):
            mixins = [mixins]
        if attr is None:
            attr={} 

        if cls.top():
            classes=[cls] + mixins + [cls.top()]
        else:
            classes=mixins + [cls] 

        return type("_".join([x.__name__ for x in classes]), tuple(classes), attr)
    
    @classmethod
    def top(cls):
        return None

#Es otra idea que no terminó de convencerme pero no la quiero borrar aun
def memoized(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        name = f"_{func.__name__}"
        print(f"searching {name}")
        value = getattr(self, name)
        if value is None:
            value = func(self, *args, **kwargs)
            setattr(self, name, value)
        return value
    return wrapper



