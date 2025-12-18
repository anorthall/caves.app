locals {
  caves_app_records = {
    "caves.app"          = { ipv4 = local.server_ipv4, ipv6 = local.server_ipv6 }
    "www.caves.app"      = { ipv4 = local.server_ipv4, ipv6 = local.server_ipv6 }
    "imgproxy.caves.app" = { ipv4 = local.server_ipv4, ipv6 = local.server_ipv6 }
  }

  caves_app_cnames = {
    "images.caves.app" = module.images_cdn.cloudfront_distribution_domain_name
    "cdn.caves.app"    = module.cdn.cloudfront_distribution_domain_name
    "status.caves.app" = "page.updown.io"
  }
}

resource "aws_route53_delegation_set" "caves_app" {
  reference_name = "caves_app_delegation_set"
}

resource "aws_route53_zone" "caves_app" {
  name              = "caves.app"
  delegation_set_id = aws_route53_delegation_set.caves_app.id
}

output "caves_app_ns" {
  value = aws_route53_zone.caves_app.name_servers
}

resource "aws_route53_record" "caves_app_a" {
  for_each = local.caves_app_records

  zone_id = aws_route53_zone.caves_app.zone_id
  name    = each.key
  type    = "A"
  ttl     = local.default_ttl
  records = [each.value.ipv4]
}

resource "aws_route53_record" "caves_app_aaaa" {
  for_each = local.caves_app_records

  zone_id = aws_route53_zone.caves_app.zone_id
  name    = each.key
  type    = "AAAA"
  ttl     = local.default_ttl
  records = [each.value.ipv6]
}

resource "aws_route53_record" "caves_app_cname" {
  for_each = local.caves_app_cnames

  zone_id = aws_route53_zone.caves_app.zone_id
  name    = each.key
  type    = "CNAME"
  ttl     = local.default_ttl
  records = [each.value]
}

resource "aws_route53_record" "mx_caves_app" {
  zone_id = aws_route53_zone.caves_app.zone_id
  name    = "caves.app"
  type    = "MX"
  ttl     = local.default_ttl
  records = [
    "10 in1-smtp.messagingengine.com.",
    "20 in2-smtp.messagingengine.com."
  ]
}

resource "aws_route53_record" "spf_caves_app" {
  zone_id = aws_route53_zone.caves_app.zone_id
  name    = "caves.app"
  type    = "TXT"
  ttl     = local.default_ttl
  records = ["v=spf1 include:amazonses.com include:spf.messagingengine.com -all"]
}

resource "aws_route53_record" "dmarc_caves_app" {
  zone_id = aws_route53_zone.caves_app.zone_id
  name    = "_dmarc.caves.app"
  type    = "TXT"
  ttl     = local.default_ttl
  records = ["v=DMARC1; p=quarantine; rua=mailto:admin@caves.app; ruf=mailto:admin@caves.app; fo=1"]
}


resource "aws_route53_record" "fastmail_domainkey" {
  count   = 3
  zone_id = aws_route53_zone.caves_app.zone_id
  name    = "fm${count.index + 1}._domainkey.caves.app"
  type    = "CNAME"
  ttl     = local.default_ttl
  records = ["fm${count.index + 1}.caves.app.dkim.fmhosted.com"]
}

resource "aws_route53_record" "caves_app_dkim" {
  for_each = toset(aws_sesv2_email_identity.caves_app.dkim_signing_attributes[0].tokens)

  zone_id = aws_route53_zone.caves_app.zone_id
  name    = "${each.value}._domainkey.caves.app"
  type    = "CNAME"
  ttl     = local.default_ttl
  records = ["${each.value}.dkim.amazonses.com"]
}

resource "aws_route53_record" "caves_app_mail_from" {
  zone_id = aws_route53_zone.caves_app.zone_id
  name    = local.ses_mail_from_domain
  type    = "MX"
  ttl     = local.default_ttl
  records = ["10 feedback-smtp.us-east-1.amazonses.com"]
}

resource "aws_route53_record" "caves_app_mail_from_spf" {
  zone_id = aws_route53_zone.caves_app.zone_id
  name    = local.ses_mail_from_domain
  type    = "TXT"
  ttl     = local.default_ttl
  records = ["v=spf1 include:amazonses.com ~all"]
}

resource "aws_route53_record" "updown_status_caves_app_txt" {
  zone_id = aws_route53_zone.caves_app.zone_id
  name    = "_updown.status.caves.app"
  type    = "TXT"
  ttl     = local.default_ttl
  records = ["updown-page=p/qj0wh"]
}
