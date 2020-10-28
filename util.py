import os

def get_path(path):
    return os.path.join(*path.split("/"))
