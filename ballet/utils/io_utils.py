import os
import shutil


def makeDir(path: str) -> None:
    if not os.path.isdir(path):
        os.makedirs(path)


def delDir(path: str) -> None:
    if os.path.isdir(path):
        shutil.rmtree(path)
