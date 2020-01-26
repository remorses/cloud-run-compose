import fire
import random
from populate import populate_string
import os.path
from .support import load, temporary_write, subprocess_call, ProcessException, dump_env_file
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
        command = "${{ command }}"
        args = "${{ args }}"
        env = [
            ${{
                indent_to('            ', '\n'.join(['{\n    name = "' + name + '"\n    value = "' + value + '"\n},' for name, value in environment.items()]))
            }}
        ]
      }
    }
  }
}


output "${{serviceName}}service_url" {
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


def main(
    projectId="pp1",
    file="docker-compose.yml",
    region="us-central1",
    credentials="credentials.json",
):
    config = yaml.safe_load(open(file))
    plan = populate_string(
        CREDENTIALS, dict(region=region, projectId=projectId, credentials=credentials)
    )
    for serviceName, service in config.get("services", {}).items():
        vars = dict(
            environment=get_environment(service),
            serviceName=serviceName,
            image=service.get("image", ""),
            command=service.get("entrypoint", ""),
            args=service.get("command", ""),
            region=region,
            projectId=projectId,
        )
        populated_service = populate_string(SERVICE_PLAN, vars)
        plan += "\n" + populated_service
        plan += populate_string(PUBLIC_SERVICE, dict(serviceName=serviceName))
    # print(plan)
    # random_dir = str(random.random())[3:]
    with open('main.tf', 'w') as f:
        f.write(plan)
    try:
        out = subprocess_call("terraform init")
        assert not out
        print(out)
        out = subprocess_call("terraform refresh")
        assert not out
        print('run terraform apply to execute the plan')
    except Exception as e:
        print(e)
        


fire.Fire(main)

