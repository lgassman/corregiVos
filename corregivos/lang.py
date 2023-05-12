from abc import ABC
from functools import wraps


class Mixable(ABC):

    
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

        print(f"{'_'.join([x.__name__ for x in classes])}, {tuple(classes)}, {attr}")
        return type("_".join([x.__name__ for x in classes]), tuple(classes), attr)
    
    @classmethod
    def top(cls):
        return None


def memoized(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        name = f"_$_{func.__name__}"
        print(f"searching {name}")
        value = getattr(self, name)
        if value is None:
            value = func(self, *args, **kwargs)
            setattr(self, name, value)
        return value
    return wrapper



