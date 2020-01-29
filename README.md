# cloud-run-compose

Deploy a stack of services to Cloud Rus using the docker-compose syntax.

Creates a terraform plan based on the docker-compose configuration.

Missing docker-compose features
- service discovery
- volumes
- non https traffic


## Install

```
pip3 install cloud-run-compose
```

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

The services will be deployed in google cloud run and will be available at url like

`https://{service-name}-zakzcx4zxq-uc.a.run.app`

## Build and push

If you want to also build and push the services you can use the `--build` flag, it will

-   build the service using the docker-compose cache
-   push the image

`compose --build --project {your-project} --credentials ./account.json`
