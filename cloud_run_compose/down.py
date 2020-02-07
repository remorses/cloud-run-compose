import os.path
from .generate_terraform import generate_terraform
import random
from .support import subprocess_call, SERVICE_URL_POSTFIX, here, terraform_space
import json


def down(
    file="docker-compose.yml",
    project="",
    region="us-central1",
    credentials="credentials.json",
    build=False,
    bucket=None,
    stack_name="",
):
    try:
        plan = generate_terraform(
            file=file,
            project=project,
            region=region,
            credentials=credentials,
            build=build,
            bucket=bucket,
            stack_name=stack_name,
        )
        with terraform_space(plan):
            out, _, _ = subprocess_call("terraform plan -compact-warnings -destroy")
            assert not out
            out, _, _ = subprocess_call("terraform destroy -auto-approve")
            assert not out
            # return urls
    except Exception as e:
        print(e)

