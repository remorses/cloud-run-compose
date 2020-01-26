import shutil
import os
import subprocess
import random
from dotenv import dotenv_values


def dump_env_file(path):
    return dotenv_values(path)


def load(path):
    with open(path) as f:
        return f.read()


class ProcessException(Exception):
    message: str

    def __init__(self, err, out):
        self.message = err + out


def subprocess_call(cmd, verbose=True, errorprint=True):
    """ Executes the given subprocess command."""

    popen_params = {
        "stdout": subprocess.PIPE,
        "stderr": subprocess.PIPE,
        "stdin": subprocess.DEVNULL,
        "shell": True,
    }
    # pretty_cmd = ' '.join(cmd)
    # print(f'executing {pretty_cmd}')
    process = subprocess.Popen(cmd, **popen_params)

    while True:
        output = process.stdout.readline()
        err = process.stderr.readline()
        if process.poll() is not None and output == b"" and err == b"":
            break
        if output:
            print(output.decode(), end="")
        if err:
            print(err.decode(), end="")
    return process.poll()


class temporary_write:
    def __init__(self, data, path=None, delete_dir=False):
        path = path or str(random.random())[3:]
        dir = os.path.dirname(path)
        if dir and not os.path.exists(dir):
            os.makedirs(dir)
        self.delete_dir = delete_dir
        self.path = os.path.abspath(path)
        self.data = data
        f = open(self.path, "w")
        f.write(self.data)
        f.close()

    __enter__ = lambda self: self.path

    def __exit__(self, a, b, c):
        if not self.delete_dir:
            os.remove(self.path)
        else:
            shutil.rmtree(os.path.dirname(self.path))
