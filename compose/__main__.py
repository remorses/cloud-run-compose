import fire
import random
from populate import populate_string
import os.path
from .support import load, temporary_write, subprocess_call
import yaml

here = os.path.dirname(__file__)


def render_terraform_plan(config):
    plan = load(os.path.join(here, "main.tf"))
    populated_plan = populate_string(plan, {"x": "XXX"})
    # print(populated_plan)
    random_dir = str(random.random())[3:]
    with temporary_write(
        populated_plan, delete_dir=True, path=os.path.join(here, random_dir, "main.tf")
    ) as plan_path:
        out = subprocess_call("ls " + plan_path)
        print(out)
        # pass


def main(file="docker-compose.yml"):
    config = yaml.safe_load(open(file))
    render_terraform_plan(config)


fire.Fire(main)

