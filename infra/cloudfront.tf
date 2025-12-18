module "cdn" {
  source  = "terraform-aws-modules/cloudfront/aws"
  version = "6.0.2"

  enabled         = true
  aliases         = ["cdn.caves.app"]
  price_class     = "PriceClass_All"
  is_ipv6_enabled = true

  origin_access_control = {
    caves_app_bucket = {
      description      = "CloudFront access to caves.app S3 bucket"
      origin_type      = "s3"
      signing_behavior = "always"
      signing_protocol = "sigv4"
    }
  }

  origin = {
    caves_app_bucket = {
      domain_name               = module.caves_app_bucket.s3_bucket_bucket_regional_domain_name
      origin_access_control_key = "caves_app_bucket"
    }
  }

  default_cache_behavior = {
    allowed_methods        = ["GET", "HEAD", "OPTIONS"]
    cached_methods         = ["GET", "HEAD"]
    target_origin_id       = "caves_app_bucket"
    viewer_protocol_policy = "redirect-to-https"
    min_ttl                = 0
    default_ttl            = 1209600  # 2 weeks
    max_ttl                = 31536000 # 1 year
    query_string           = true
    compress               = true
  }

  viewer_certificate = {
    acm_certificate_arn = module.caves_app_certificate.acm_certificate_arn
    ssl_support_method  = "sni-only"
  }

  providers = {
    aws = aws.use1
  }
}

module "images_cdn" {
  source  = "terraform-aws-modules/cloudfront/aws"
  version = "6.0.2"

  enabled         = true
  aliases         = ["images.caves.app"]
  price_class     = "PriceClass_All"
  is_ipv6_enabled = true

  origin = {
    imgproxy_caver_dev = {
      domain_name = "imgproxy.caver.dev"
      custom_origin_config = {
        http_port              = 80
        https_port             = 443
        origin_protocol_policy = "https-only"
        origin_ssl_protocols   = ["TLSv1.2"]
      }
    }
  }

  default_cache_behavior = {
    allowed_methods        = ["GET", "HEAD", "OPTIONS"]
    cached_methods         = ["GET", "HEAD"]
    target_origin_id       = "imgproxy_caver_dev"
    viewer_protocol_policy = "redirect-to-https"
    min_ttl                = 0
    default_ttl            = 1209600  # 2 weeks
    max_ttl                = 31536000 # 1 year
    query_string           = true
    compress               = true
  }

  viewer_certificate = {
    acm_certificate_arn = module.caves_app_certificate.acm_certificate_arn
    ssl_support_method  = "sni-only"
  }

  providers = {
    aws = aws.use1
  }
}

module "caves_app_certificate" {
  source  = "terraform-aws-modules/acm/aws"
  version = "6.2.0"

  domain_name               = "caves.app"
  subject_alternative_names = ["*.caves.app"]
  zone_id                   = aws_route53_zone.caves_app.zone_id

  validation_method = "DNS"

  providers = {
    aws = aws.use1
  }
}
