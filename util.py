import os

def get_path(path):
    return os.path.join(*path.split("/"))

def get_all_subclasses(cls):
    return set(cls.__subclasses__()).union(
        [s for c in cls.__subclasses__() for s in all_subclasses(c)])
