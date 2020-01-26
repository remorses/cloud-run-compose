

provider "google-beta" {
  credentials = file("account.json")
  project     = "molten-enigma-261612"
  region      = "us-central1"
}

provider "google" {
  credentials = file("account.json")
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


resource "google_cloud_run_service" "example-cloudrun-compose" {
  provider = google-beta
  name     = "example-cloudrun-compose"
  location = "us-central1"
  metadata {
    namespace = "molten-enigma-261612"
  }

  template {
    spec {
      containers {
        image = "gcr.io/cloudrun/hello"
        
        

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


output "example-cloudrun-compose_service_url" {
  value = "${google_cloud_run_service.example-cloudrun-compose.status[0].url}"
}

resource "google_cloud_run_service_iam_policy" "example-cloudrun-compose_noauth" {
  location    = google_cloud_run_service.example-cloudrun-compose.location
  project     = google_cloud_run_service.example-cloudrun-compose.project
  service     = google_cloud_run_service.example-cloudrun-compose.name

  policy_data = data.google_iam_policy.noauth.policy_data
}
