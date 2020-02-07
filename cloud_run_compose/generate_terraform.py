import fire
import shutil
import json
from funcy import drop, pluck
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
    SERVICE_URL_POSTFIX,
)
import yaml


REMOTE_STATE = r"""
terraform {
  backend "gcs" {
    bucket      = "${{ bucket }}"
    prefix      = "terraform_states/${{stack_name}}"
    credentials = "${{ credentials }}"
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
    metadata {
        annotations = {
            "autoscaling.knative.dev/maxScale" = "1000"
        }
        labels      = {}
    }
    spec {
      container_concurrency = 80 
      containers {
        image = "${{ image }}"
        resources {
            limits   = {
                cpu    = "1000m"
                memory = "256M"
            }
            requests = {}
        }
        ${{ f'command = {json.dumps(command)}' if command else '' }}
        ${{ f'args = {json.dumps(args)}' if args else '' }}

        ${{
            indent_to('        ', '\n'.join(['env {\n    name = "' + name + '"\n    value = "' + value + '"\n}\n' for name, value in environment.items()]))
        }}
      }
    }
  }
}


output "${{output_url}}" {
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


def generate_terraform(file, project, region, credentials, build, bucket, stack_name):
    assert project
    credentials = os.path.abspath(credentials)
    file = os.path.abspath(file)
    try:
        data = get_stdout(f"docker-compose -f {file} config")
    except ProcessException as e:
        printred(e.message)
        return
    config = yaml.safe_load(data)
    if not stack_name:
        stack_name = os.path.basename(
            os.path.normpath(os.path.abspath(os.path.dirname(file)))
        )
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

        variables = dict(
            environment=get_environment(service),
            service_name=stack_name + service_name,
            image=service.get("image", ""),
            command=parse_command(service.get("entrypoint", [])),
            args=parse_command(service.get("command", [])),
            region=region,
            projectId=project,
            output_url=stack_name + service_name + SERVICE_URL_POSTFIX,
        )
        populated_service = populate_string(SERVICE_PLAN, variables)
        plan += "\n" + populated_service
        plan += populate_string(
            PUBLIC_SERVICE, dict(service_name=stack_name + service_name)
        )
    return plan

