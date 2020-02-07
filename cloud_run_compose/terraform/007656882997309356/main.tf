
terraform {
  backend "gcs" {
    bucket      = "example_shit_1"
    prefix      = "terraform_states/cloudrun-compose"
    credentials = "/Users/morse/Documents/GitHub/cloudrun-compose/account.json"
  }
}



provider "google-beta" {
  credentials = file("/Users/morse/Documents/GitHub/cloudrun-compose/account.json")
  project     = "molten-enigma-261612"
  region      = "us-central1"
}

provider "google" {
  credentials = file("/Users/morse/Documents/GitHub/cloudrun-compose/account.json")
  project     = "molten-enigma-261612"
  region      = "us-central1"
}

data "google_iam_policy" "noauth" {
  binding {
    role = "roles/run.invoker"
    members = [
      "allUsers",
    ]
  }
}


resource "google_cloud_run_service" "cloudrun-composeexample-cloudrun-compose" {
  provider = google-beta
  name     = "cloudrun-composeexample-cloudrun-compose"
  location = "us-central1"
  metadata {
    namespace = "molten-enigma-261612"
  }

  template {
    metadata {
        annotations = {
            "autoscaling.knative.dev/maxScale" = "1000"
        }
        generation  = 0
        labels      = {}
    }
    spec {
      container_concurrency = 80 
      containers {
        image = "gcr.io/cloudrun/hello"
        resources {
            limits   = {
                cpu    = "1000m"
                memory = "256M"
            }
            requests = {}
        }
        
        

        env {
            name = "URL_0"
            value = "http://mongoke/"
        }
        env {
            name = "URL_1"
            value = "http://server"
        }
      }
    }
  }
}


output "cloudrun-composeexample-cloudrun-compose_service_url" {
  value = "${google_cloud_run_service.cloudrun-composeexample-cloudrun-compose.status[0].url}"
}

resource "google_cloud_run_service_iam_policy" "cloudrun-composeexample-cloudrun-compose_noauth" {
  location    = google_cloud_run_service.cloudrun-composeexample-cloudrun-compose.location
  project     = google_cloud_run_service.cloudrun-composeexample-cloudrun-compose.project
  service     = google_cloud_run_service.cloudrun-composeexample-cloudrun-compose.name

  policy_data = data.google_iam_policy.noauth.policy_data
}
