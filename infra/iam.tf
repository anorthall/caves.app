resource "aws_iam_user" "caves_app" {
  name = "caves_app"
}

resource "aws_iam_access_key" "caves_app" {
  user = aws_iam_user.caves_app.name
}

output "caves_app_access_key" {
  value = aws_iam_access_key.caves_app.id
}

output "caves_app_secret_access_key" {
  value     = aws_iam_access_key.caves_app.secret
  sensitive = true
}

resource "aws_iam_user_policy_attachment" "caves_app_bucket_read_write" {
  user       = aws_iam_user.caves_app.name
  policy_arn = aws_iam_policy.caves_app_bucket_read_write.arn
}

resource "aws_iam_policy" "caves_app_bucket_read_write" {
  name   = "caves_app_bucket_read_write"
  policy = data.aws_iam_policy_document.caves_app_bucket_read_write_policy.json
}

resource "aws_iam_user_policy_attachment" "caves_app_ses" {
  user       = aws_iam_user.caves_app.name
  policy_arn = aws_iam_policy.caves_app_ses.arn
}

resource "aws_iam_policy" "caves_app_ses" {
  name   = "caves_app_ses"
  policy = data.aws_iam_policy_document.ses_policy.json
}

data "aws_iam_policy_document" "caves_app_bucket_read_write_policy" {
  statement {
    effect = "Allow"
    actions = [
      "s3:ListBucket",
      "s3:GetObject",
      "s3:PutObject",
      "s3:DeleteObject",
      "s3:DeleteObjectVersion",
      "s3:GetBucketLocation",
      "s3:ListBucketMultipartUploads",
      "s3:AbortMultipartUpload",
      "s3:ListMultipartUploadParts"
    ]
    resources = [
      module.caves_app_bucket.s3_bucket_arn,
      "${module.caves_app_bucket.s3_bucket_arn}/*",
      module.caves_app_backups_bucket.s3_bucket_arn,
      "${module.caves_app_backups_bucket.s3_bucket_arn}/*"
    ]
  }
}

data "aws_iam_policy_document" "ses_policy" {
  statement {
    effect = "Allow"
    actions = [
      "ses:SendEmail",
      "ses:SendRawEmail"
    ]
    resources = ["*"]
  }
}
