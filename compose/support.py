import shutil
import os
import subprocess
import random


def load(path):
    with open(path) as f:
        return f.read()


def subprocess_call(cmd, verbose=True, errorprint=True):
    """ Executes the given subprocess command."""

    popen_params = {
        "stdout": subprocess.PIPE,
        "stderr": subprocess.PIPE,
        "stdin": subprocess.DEVNULL,
        'shell': True
    }
    # pretty_cmd = ' '.join(cmd)
    # print(f'executing {pretty_cmd}')
    proc = subprocess.Popen(cmd, **popen_params)

    out, err = proc.communicate()
    # print(out)
    # proc.stderr.close()

    if proc.returncode:
        raise Exception(err.decode("utf8"), out.decode("utf8"))

    del proc
    return out.decode("utf8")


class temporary_write:
    def __init__(self, data, path=None, delete_dir=False):
        path = path or str(random.random())[3:]
        dir = os.path.dirname(path)
        if not os.path.exists(dir):
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
        
