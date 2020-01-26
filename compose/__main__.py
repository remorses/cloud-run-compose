import fire
import random
from populate import populate_string
import os.path
from .support import load, temporary_write, subprocess_call
import yaml

here = os.path.dirname(__file__)

CREDENTIALS = """

provider "google-beta" {
  credentials = file("${{ credentials }}")
  project     = "${{projectId}}"
  region      = "${{region}}
}

provider "google" {
  credentials = file("${{ credentials }}")
  project     = "${{projectId}}"
  region      = "${{region}}
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

PUBLIC_SERVICE = """
resource "google_cloud_run_service_iam_policy" "${{serviceName}}_noauth" {
  location    = google_cloud_run_service.${{serviceName}}.location
  project     = google_cloud_run_service.${{serviceName}}.project
  service     = google_cloud_run_service.${{serviceName}}.name

  policy_data = data.google_iam_policy.noauth.policy_data
}
"""

# plan = load(os.path.join(here, "main.tf"))


def get_environment(config):
    env = config.get("environment")
    if isinstance(env, dict):
        return env
    if isinstance(env, list):
        result = {}
        for line in env:
            k, _, v = line.partition("=")
            result[k] = v
        return result
    return {}


def main(
    projectId="pp1",
    file="docker-compose.yml",
    region="us-central1",
    credentials="credential.json",
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
    print(plan)
    # random_dir = str(random.random())[3:]
    # with temporary_write(
    #     populated_plan, delete_dir=True, path=os.path.join(here, random_dir, "main.tf")
    # ) as plan_path:
    #     out = subprocess_call("cat " + plan_path)
    #     print(out)


fire.Fire(main)

