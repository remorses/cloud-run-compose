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
    printblue
)
import yaml


here = os.path.dirname(__file__)

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
resource "google_cloud_run_service" "${{ serviceName }}" {
  provider = google-beta
  name     = "${{ serviceName }}"
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


output "${{serviceName}}_service_url" {
  value = "${google_cloud_run_service.${{serviceName}}.status[0].url}"
}
"""

PUBLIC_SERVICE = r"""
resource "google_cloud_run_service_iam_policy" "${{serviceName}}_noauth" {
  location    = google_cloud_run_service.${{serviceName}}.location
  project     = google_cloud_run_service.${{serviceName}}.project
  service     = google_cloud_run_service.${{serviceName}}.name

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
    build=False
):
    try:
        data = get_stdout(f"docker-compose -f {file} config")
    except ProcessException as e:
        printred(e.message)
        return
    config = yaml.safe_load(data)
    plan = populate_string(
        CREDENTIALS, dict(region=region, projectId=project, credentials=credentials)
    )
    for serviceName, service in config.get("services", {}).items():
        if not service.get('image'):
            printred('all services need an image to be deployed to Cloud Run')
            return
        if build and service.get('build'):
            code, _, _ = subprocess_call(f'docker-compose -f {file} build {serviceName}')
            if code:
                printred('failed building')
                return
            print('pushing to registry')
            code, _, _ = subprocess_call(f'docker-compose -f {file} push {serviceName}')
            if code:
                printred('cannot push image')
                return

        vars = dict(
            environment=get_environment(service),
            serviceName=serviceName,
            image=service.get("image", ""),
            command=parse_command(service.get("entrypoint", [])),
            args=parse_command(service.get("command", [])),
            region=region,
            projectId=project,
        )
        populated_service = populate_string(SERVICE_PLAN, vars)
        plan += "\n" + populated_service
        plan += populate_string(PUBLIC_SERVICE, dict(serviceName=serviceName))
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




