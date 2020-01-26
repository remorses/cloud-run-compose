

provider "google-beta" {
  credentials = file("credentials.json")
  project     = "pp1"
  region      = "us-central1"
}

provider "google" {
  credentials = file("credentials.json")
  project     = "pp1"
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


resource "google_cloud_run_service" "mongoke" {
  provider = google-beta
  name     = "mongoke"
  location = "us-central1"
  metadata {
    namespace = "pp1"
  }

  template {
    spec {
      containers {
        image = "mongoke/mongoke:latest"
        command = ""
        args = ""
        env = [
            {
                name = "DEBUG"
                value = "1"
            },
            {
                name = "DB_URL"
                value = "mongodb://mongo/db"
            },
        ]
      }
    }
  }
}


output "mongokeservice_url" {
  value = "${google_cloud_run_service.mongoke.status[0].url}"
}

resource "google_cloud_run_service_iam_policy" "mongoke_noauth" {
  location    = google_cloud_run_service.mongoke.location
  project     = google_cloud_run_service.mongoke.project
  service     = google_cloud_run_service.mongoke.name

  policy_data = data.google_iam_policy.noauth.policy_data
}


resource "google_cloud_run_service" "mongo" {
  provider = google-beta
  name     = "mongo"
  location = "us-central1"
  metadata {
    namespace = "pp1"
  }

  template {
    spec {
      containers {
        image = "mongo"
        command = ""
        args = ""
        env = [
            
        ]
      }
    }
  }
}


output "mongoservice_url" {
  value = "${google_cloud_run_service.mongo.status[0].url}"
}

resource "google_cloud_run_service_iam_policy" "mongo_noauth" {
  location    = google_cloud_run_service.mongo.location
  project     = google_cloud_run_service.mongo.project
  service     = google_cloud_run_service.mongo.name

  policy_data = data.google_iam_policy.noauth.policy_data
}


resource "google_cloud_run_service" "upload" {
  provider = google-beta
  name     = "upload"
  location = "us-central1"
  metadata {
    namespace = "pp1"
  }

  template {
    spec {
      containers {
        image = "xmorse/s3-filepond"
        command = ""
        args = ""
        env = [
            {
                name = "ENDPOINT"
                value = "https://storage.googleapis.com"
            },
            {
                name = "AWS_ACCESS_KEY_ID"
                value = "$ACCESS_KEY_ID"
            },
            {
                name = "AWS_SECRET_ACCESS_KEY"
                value = "$SECRET_ACCESS_KEY"
            },
            {
                name = "DIRECTORY"
                value = "efi-archives/"
            },
            {
                name = "BUCKET"
                value = "efi-archives"
            },
            {
                name = "REGION"
                value = "eu-west-1"
            },
        ]
      }
    }
  }
}


output "uploadservice_url" {
  value = "${google_cloud_run_service.upload.status[0].url}"
}

resource "google_cloud_run_service_iam_policy" "upload_noauth" {
  location    = google_cloud_run_service.upload.location
  project     = google_cloud_run_service.upload.project
  service     = google_cloud_run_service.upload.name

  policy_data = data.google_iam_policy.noauth.policy_data
}
