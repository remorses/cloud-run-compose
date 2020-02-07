import shutil
import sys
import os
import pexpect
import subprocess
import random
from dotenv import dotenv_values
from colorama import Fore, Back, Style, init
from contextlib import contextmanager

init()
SERVICE_URL_POSTFIX = "_service_url"
here = os.path.abspath(os.path.dirname(__file__))

TF_CLI_CONFIG_FILE = os.path.join(here, ".terraformrc")
PLUGINS_DIR = os.path.join(here, "plugins")
os.makedirs(PLUGINS_DIR, exist_ok=True)
with open(TF_CLI_CONFIG_FILE, "w") as f:
    f.write(f'plugin_cache_dir = "{PLUGINS_DIR}"')


def valid_name(s):
    return any(not c.isalnum() or c != "-" for c in s)


def get_child(parent):
    for o in os.listdir(parent):
        if os.path.isdir(os.path.join(parent, o)):
            return os.path.abspath(os.path.join(parent, o))


@contextmanager
def terraform_space(plan):
    old_cwd = os.path.abspath(".")
    hash = str(random.random()).replace(".", "")[:7]
    cwd = os.path.join(here, "terraform", hash)
    try:
        os.makedirs(cwd, exist_ok=True)
        os.chdir(cwd)
        with open("main.tf", "w") as f:
            f.write(plan)
        # plugin_dir = os.path.abspath(os.path.join(here, "plugins"))

        plugins_dir = get_child(PLUGINS_DIR)
        if not plugins_dir:
            out, _, _ = subprocess_call(f"terraform init")
            assert not out
        else:
            out, _, _ = subprocess_call(f"terraform init -plugin-dir {plugins_dir}")
            assert not out
        yield None
    except Exception as e:
        raise e
    finally:
        os.chdir(old_cwd)
        shutil.rmtree(cwd)


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


def subprocess_call(cmd, silent=False):
    """ Executes the given subprocess command."""

    popen_params = {
        "stdout": subprocess.PIPE,
        "stderr": subprocess.STDOUT,
        "shell": True,
        "env": {
            **os.environ,
            "TF_IN_AUTOMATION": "1",
            "TF_CLI_CONFIG_FILE": TF_CLI_CONFIG_FILE,
        },
    }
    # pretty_cmd = ' '.join(cmd)
    # print(f'executing {pretty_cmd}')
    process = subprocess.Popen(cmd, **popen_params)
    result1 = ""
    result2 = ""
    while True:
        output = process.stdout.readline()
        # err = process.stderr.readline()
        err = ""
        if output == b"":
            break

        if output:
            if not silent:
                sys.stdout.write(output.decode())
                sys.stdout.flush()
            result1 += output.decode()
        if err:
            if not silent:
                sys.stderr.write(err.decode())
                sys.stderr.flush()
            result2 += err.decode()
    return process.returncode, result1, result2


def get_stdout(cmd,):
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
