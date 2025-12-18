module "caves_app_bucket" {
  source  = "terraform-aws-modules/s3-bucket/aws"
  version = "5.9.1"

  bucket = "cavesapp"

  control_object_ownership = true
  object_ownership         = "BucketOwnerEnforced"

  attach_policy = true
  policy        = data.aws_iam_policy_document.caves_app_bucket_policy.json

  versioning = {
    enabled = true
  }
}

data "aws_iam_policy_document" "caves_app_bucket_policy" {
  statement {
    effect = "Allow"
    principals {
      type        = "Service"
      identifiers = ["cloudfront.amazonaws.com"]
    }
    actions   = ["s3:GetObject"]
    resources = ["${module.caves_app_bucket.s3_bucket_arn}/*"]
    condition {
      test     = "StringEquals"
      variable = "AWS:SourceArn"
      values   = [module.cdn.cloudfront_distribution_arn]
    }
  }
}

module "caves_app_backups_bucket" {
  source  = "terraform-aws-modules/s3-bucket/aws"
  version = "5.9.1"

  bucket = "cavesapp-backups"

  control_object_ownership = true
  object_ownership         = "BucketOwnerEnforced"

  versioning = {
    enabled = true
  }
}
