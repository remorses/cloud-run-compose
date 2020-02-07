import fire
import random
from populate import populate_string
import os.path
from .support import (
    load,
    temporary_write,
    subprocess_call,
    ProcessException,
    dump_env_file,
    get_stdout,
    printred,
    printblue,
)
import yaml


here = os.path.dirname(__file__)

REMOTE_STATE = r"""
terraform {
  backend "gcs" {
    bucket      = "${{ bucket }}"
    prefix      = "terraform_states/${{stack_name}}"
    credentials = file("${{ credentials }}")
  }
}

"""


CREDENTIALS = r"""

provider "google-beta" {
  credentials = file("${{ credentials }}")
  project     = "${{projectId}}"
  region      = "${{region}}"
}

provider "google" {
  credentials = file("${{ credentials }}")
  project     = "${{projectId}}"
  region      = "${{region}}"
}

data "google_iam_policy" "noauth" {
  binding {
    role = "roles/run.invoker"
    members = [
      "allUsers",
    ]
  }
}
"""


SERVICE_PLAN = r"""
resource "google_cloud_run_service" "${{ service_name }}" {
  provider = google-beta
  name     = "${{ service_name }}"
  location = "${{ region }}"
  metadata {
    namespace = "${{ projectId }}"
  }

  template {
    spec {
      containers {
        image = "${{ image }}"
        ${{ f'command = {json.dumps(command)}' if command else '' }}
        ${{ f'args = {json.dumps(args)}' if args else '' }}

        ${{
            indent_to('        ', '\n'.join(['env {\n    name = "' + name + '"\n    value = "' + value + '"\n}\n' for name, value in environment.items()]))
        }}
      }
    }
  }
}


output "${{service_name}}_service_url" {
  value = "${google_cloud_run_service.${{service_name}}.status[0].url}"
}
"""

PUBLIC_SERVICE = r"""
resource "google_cloud_run_service_iam_policy" "${{service_name}}_noauth" {
  location    = google_cloud_run_service.${{service_name}}.location
  project     = google_cloud_run_service.${{service_name}}.project
  service     = google_cloud_run_service.${{service_name}}.name

  policy_data = data.google_iam_policy.noauth.policy_data
}
"""

# plan = load(os.path.join(here, "main.tf"))


def get_environment(config):
    result = {}
    env_files = config.get("env_file")
    if isinstance(env_files, list):
        for path in env_files:
            result.update(dump_env_file(path))
    elif isinstance(env_files, str):
        result.update(dump_env_file(env_files))

    env = config.get("environment")
    if isinstance(env, dict):
        result.update(env)
    if isinstance(env, list):
        for line in env:
            k, _, v = line.partition("=")
            result[k] = v
    return result


def parse_command(command):
    if isinstance(command, list):
        return command
    if isinstance(command, str):
        return ["sh", "-c", command]
    raise Exception(f"cannot transform command `{command}` to list")


def main(
    file="docker-compose.yml",
    project="pp1",
    region="us-central1",
    credentials="credentials.json",
    output_plan="main.tf",
    build=False,
    bucket=None,
    stack_name="",
):
    try:
        data = get_stdout(f"docker-compose -f {file} config")
    except ProcessException as e:
        printred(e.message)
        return
    config = yaml.safe_load(data)
    if not stack_name:
        stack_name = os.path.dirname(file).split("/")[-1]
    if bucket:  # TODO use other bucket provider than gcp
        plan = populate_string(
            REMOTE_STATE,
            dict(credentials=credentials, bucket=bucket, stack_name=stack_name),
        )
    plan += populate_string(
        CREDENTIALS, dict(region=region, projectId=project, credentials=credentials)
    )
    for service_name, service in config.get("services", {}).items():
        if not service.get("image"):
            printred("all services need an image to be deployed to Cloud Run")
            return
        if build and service.get("build"):
            code, _, _ = subprocess_call(
                f"docker-compose -f {file} build {service_name}"
            )
            if code:
                printred("failed building")
                return
            print("pushing to registry")
            code, _, _ = subprocess_call(
                f"docker-compose -f {file} push {service_name}"
            )
            if code:
                printred("cannot push image")
                return

        vars = dict(
            environment=get_environment(service),
            service_name=stack_name + service_name,
            image=service.get("image", ""),
            command=parse_command(service.get("entrypoint", [])),
            args=parse_command(service.get("command", [])),
            region=region,
            projectId=project,
        )
        populated_service = populate_string(SERVICE_PLAN, vars)
        plan += "\n" + populated_service
        plan += populate_string(
            PUBLIC_SERVICE, dict(serviceName=stack_name + service_name)
        )
    # print(plan)
    # random_dir = str(random.random())[3:]
    with open(output_plan, "w") as f:
        f.write(plan)
    try:
        out, _, _ = subprocess_call("terraform init")
        assert not out
        out, _, _ = subprocess_call("terraform refresh")
        assert not out
        printblue("run `terraform apply` to execute the plan")
    except Exception as e:
        print(e)

