# python-lib-template

## Requirements

-   `terraform` in PATH
-   `docker-compose` in PATH
-   a google cloud dervice account .json file

## Usage


Download a service account json from the console, with the cloud run persmissions, place it in `./account.json`

Use the following `docker-compose.yml` file

```yml
version: '3'

services:
    example-cloudrun-compose:
        image: gcr.io/cloudrun/hello
        expose:
            - 8080
        environment:
            URL_0: 'http://mongoke/'
            URL_1: 'http://server'
    example-cloudrun-compose2:
        image: gcr.io/cloudrun/hello
        expose:
            - 8080
```

Run the following command to deploy the services

`compose --project {your-project} --credentials ./account.json`

The command will generate a `main.tf` file in the working directory, to deploy the plan run

`terraform apply`

The services will be deployed as cloud run services in google cloud

```
google_cloud_run_service.example-cloudrun-compose: Creating...
google_cloud_run_service.example-cloudrun-compose: Still creating... [10s elapsed]
google_cloud_run_service.example-cloudrun-compose: Still creating... [20s elapsed]
google_cloud_run_service.example-cloudrun-compose: Still creating... [30s elapsed]
google_cloud_run_service.example-cloudrun-compose: Creation complete after 31s [id=locations/us-central1/namespaces/molten-enigma-261612/services/example-cloudrun-compose]
google_cloud_run_service_iam_policy.example-cloudrun-compose_noauth: Creating...
google_cloud_run_service_iam_policy.example-cloudrun-compose_noauth: Creation complete after 2s [id=v1/projects/molten-enigma-261612/locations/us-central1/services/example-cloudrun-compose]

Apply complete! Resources: 2 added, 0 changed, 0 destroyed.

Outputs:

example-cloudrun-composeservice_url = https://example-cloudrun-compose-zakzcx4zxq-uc.a.run.app
```

## Build and push

If you want to also build and push the services you can use the `--build` flag, it will

-   build the service using the docker-compose cache
-   push the image

`compose --build --project {your-project} --credentials ./account.json`
