locals {
  ses_mail_from_domain = "mail.caves.app"
}

resource "aws_sesv2_email_identity" "caves_app" {
  email_identity         = "caves.app"
  configuration_set_name = aws_ses_configuration_set.caves_app.name

  dkim_signing_attributes {
    next_signing_key_length = "RSA_2048_BIT"
  }
}

resource "aws_sesv2_email_identity_mail_from_attributes" "caves_app" {
  email_identity         = aws_sesv2_email_identity.caves_app.email_identity
  mail_from_domain       = local.ses_mail_from_domain
  behavior_on_mx_failure = "USE_DEFAULT_VALUE"
}

resource "aws_ses_configuration_set" "caves_app" {
  name = "caves-app"

  delivery_options {
    tls_policy = "Require"
  }

  reputation_metrics_enabled = true
}
