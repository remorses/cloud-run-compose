import shutil
import os
import subprocess
import random
from dotenv import dotenv_values
from colorama import Fore, Back, Style, init

init()

def printred(msg):
    print(Fore.RED + msg)
    print(Style.RESET_ALL)

def printblue(msg):
    print(Fore.YELLOW + msg)
    print(Style.RESET_ALL)

def dump_env_file(path):
    return dotenv_values(path)


def load(path):
    with open(path) as f:
        return f.read()


class ProcessException(Exception):
    message: str

    def __init__(self, err, out):
        self.message = err + out


def subprocess_call(cmd, ):
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

    result1 = ''
    result2 = ''
    while True:
        output = process.stdout.readline()
        err = process.stderr.readline()
        if process.poll() is not None and output == b"" and err == b"":
            break
        if output:
            print(output.decode(), end="")
            result1 += output.decode()
        if err:
            print(err.decode(), end="")
            result2 += err.decode()
    return process.poll(), result1, result2

def get_stdout(cmd, ):
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
    out, err = process.communicate()
    if process.returncode:
        raise ProcessException(out.decode(), err.decode())
    return out.decode()


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
