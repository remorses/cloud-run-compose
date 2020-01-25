
variable "projectId" {
  type    = string
  default = "molten-enigma-261612"
}
variable "credentialsJson" {
  type    = string
  default = "credentials.json"
}
variable "serviceName" {
  type    = string
  default = "test_terraform"
}
variable "loacation" {
  type    = string
  default = "us-central1"
}
variable "image" {
  type    = string
  default = "gcr.io/cloudrun/hello"
}

# variable "domain" {
#   type    = string
#   default = "instabotnet.club"
# }

# variable "cloud_dns_zone_name" {
#   type    = string
#   default = "instabotnet"
# }

provider "google-beta" {
  credentials = file(var.credentialsJson)
  project     = var.projectId
  region      = "us-central1"
}

provider "google" {
  credentials = file(var.credentialsJson)
  project     = var.projectId
  region      = "us-central1"
}

# variable "subdomain" {
#   type    = string
#   default = "backend"
# }

# resource "google_dns_record_set" "cname" {
#   name         = "${var.subdomain}.${var.domain}."
#   managed_zone = var.cloud_dns_zone_name
#   rrdatas      = ["ghs.googlehosted.com."]
#   type         = "CNAME"
#   ttl          = 5
# }

resource "google_cloud_run_service" "default" {
  provider = google-beta
  name     = var.serviceName
  location = var.loacation
  metadata {
    namespace = var.projectId
  }

  template {
    spec {
      containers {
        image = var.image
        command = var.command
        args = var.args
        env = [
            ${{
                indent_to('            ', '\n'.join(['{\nname = "' + name + '"\nvalue = "' + value + '"\n},' for name, value in environment.items()]))
            }}
        ]
      }
    }
  }
}

# resource "google_cloud_run_domain_mapping" "default" {
#   provider   = google-beta
#   depends_on = [google_cloud_run_service.default, google_cloud_run_service_iam_policy.noauth, google_dns_record_set.cname]
#   location   = "us-central1"
#   name       = "${var.subdomain}.${var.domain}"

#   metadata {
#     namespace = var.projectId
#   }

#   spec {
#     route_name = google_cloud_run_service.default.name
#     # force_override = true
#   }
# }

data "google_iam_policy" "noauth" {
  binding {
    role = "roles/run.invoker"
    members = [
      "allUsers",
    ]
  }
}

resource "google_cloud_run_service_iam_policy" "noauth" {
  provider    = google-beta
  location    = google_cloud_run_service.default.location
  project     = google_cloud_run_service.default.project
  service     = google_cloud_run_service.default.name
  policy_data = data.google_iam_policy.noauth.policy_data
}

# output "domain_status" {
#   value = "${google_cloud_run_domain_mapping.default.status[0].conditions[0].status}"
# }

output "service_url" {
  value = "${google_cloud_run_service.default.status[0].url}"
}
