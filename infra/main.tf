terraform {
  required_providers {
    aws = {
      source = "hashicorp/aws"
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
  server_ipv4 = "142.132.153.211"
  server_ipv6 = "2a01:4f8:261:2986::2"
}
