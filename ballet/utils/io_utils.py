import os
import shutil


def makeDir(path: str) -> bool:
    if not os.path.isdir(path):
        os.makedirs(path)
        return True
    return False


def delDir(path: str) -> bool:
    if os.path.isdir(path):
        shutil.rmtree(path)
        return True
    return False


def touch(path: str):
    # Create an empty file
    with open(path, 'w') as file:
        pass


def write(path: str, content: str):
    # Create an empty file
    with open(path, 'w') as file:
        file.write(content)