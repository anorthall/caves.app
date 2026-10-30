terraform {
  required_providers {
    aws = {
      source = "hashicorp/aws"
    }
    cloudflare = {
      source  = "cloudflare/cloudflare"
      version = "5.28.1"
    }
  }
}

provider "aws" {
  default_tags {
    tags = {
      project = "cavesapp"
    }
  }
}

provider "aws" {
  alias  = "use1"
  region = "us-east-1"
}

locals {
  default_ttl = 300
  server_ipv4 = "138.201.57.152"
  server_ipv6 = "2a01:4f8:172:1291::2"
}
