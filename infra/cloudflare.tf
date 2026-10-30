# API token is read from the CLOUDFLARE_API_TOKEN environment variable.
provider "cloudflare" {}

locals {
  cloudflare_account_id = "4355c9721c2d726f587442c478678172"
}
