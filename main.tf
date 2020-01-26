

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


resource "google_cloud_run_service" "gateway" {
  provider = google-beta
  name     = "gateway"
  location = "us-central1"
  metadata {
    namespace = "molten-enigma-261612"
  }

  template {
    spec {
      containers {
        image = "gcr.io/cloudrun/hello"
        
        args = ["sh", "-c", "bash"]

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


output "gatewayservice_url" {
  value = "${google_cloud_run_service.gateway.status[0].url}"
}

resource "google_cloud_run_service_iam_policy" "gateway_noauth" {
  location    = google_cloud_run_service.gateway.location
  project     = google_cloud_run_service.gateway.project
  service     = google_cloud_run_service.gateway.name

  policy_data = data.google_iam_policy.noauth.policy_data
}


resource "google_cloud_run_service" "test" {
  provider = google-beta
  name     = "test"
  location = "us-central1"
  metadata {
    namespace = "molten-enigma-261612"
  }

  template {
    spec {
      containers {
        image = "busybox"
        
        args = ["sh", "-c", "echo ciao"]

        
      }
    }
  }
}


output "testservice_url" {
  value = "${google_cloud_run_service.test.status[0].url}"
}

resource "google_cloud_run_service_iam_policy" "test_noauth" {
  location    = google_cloud_run_service.test.location
  project     = google_cloud_run_service.test.project
  service     = google_cloud_run_service.test.name

  policy_data = data.google_iam_policy.noauth.policy_data
}
