resource "cloudflare_zone" "caves_app" {
  account = { id = local.cloudflare_account_id }
  name    = "caves.app"
  type    = "full"
}

output "caves_app_cf_ns" {
  value = cloudflare_zone.caves_app.name_servers
}

locals {
  caves_app_cf_txts = {
    "caves.app"                  = "v=spf1 include:amazonses.com include:spf.messagingengine.com -all"
    "_dmarc.caves.app"           = "v=DMARC1; p=quarantine; rua=mailto:admin@caves.app; ruf=mailto:admin@caves.app; fo=1"
    "_updown.status.caves.app"   = "updown-page=p/qj0wh"
    (local.ses_mail_from_domain) = "v=spf1 include:amazonses.com ~all"
    # Present in Route53 but not managed by Terraform there.
    "id/nzlnoncdvynv6dwpjtm5rvjny14dplqxbf/qjlfe=.caves.app" = "id/NzLNoNCDvyNV6DWPjtM5RVjny14DPLqXBf/QjlfE="
  }

  caves_app_cf_mx = {
    "in1"       = { name = "caves.app", content = "in1-smtp.messagingengine.com", priority = 10 }
    "in2"       = { name = "caves.app", content = "in2-smtp.messagingengine.com", priority = 20 }
    "mail_from" = { name = local.ses_mail_from_domain, content = "feedback-smtp.us-east-1.amazonses.com", priority = 10 }
  }

  caves_app_cf_dkim = merge(
    { for fm in ["fm1", "fm2", "fm3"] : "${fm}._domainkey.caves.app" => "${fm}.caves.app.dkim.fmhosted.com" },
    {
      for token in aws_sesv2_email_identity.caves_app.dkim_signing_attributes[0].tokens :
      "${token}._domainkey.caves.app" => "${token}.dkim.amazonses.com"
    },
  )

  # The apex and wildcard names share a single validation record.
  caves_app_cf_acm_validation = {
    for option in module.caves_app_certificate.acm_certificate_domain_validation_options :
    trimsuffix(option.resource_record_name, ".") => trimsuffix(option.resource_record_value, ".")...
  }
}

resource "cloudflare_dns_record" "caves_app_a" {
  for_each = local.caves_app_records

  zone_id = cloudflare_zone.caves_app.id
  name    = each.key
  type    = "A"
  ttl     = local.default_ttl
  content = each.value.ipv4
  proxied = false
}

resource "cloudflare_dns_record" "caves_app_aaaa" {
  for_each = local.caves_app_records

  zone_id = cloudflare_zone.caves_app.id
  name    = each.key
  type    = "AAAA"
  ttl     = local.default_ttl
  content = each.value.ipv6
  proxied = false
}

resource "cloudflare_dns_record" "caves_app_cname" {
  for_each = merge(
    local.caves_app_cnames,
    local.caves_app_cf_dkim,
    { for name, values in local.caves_app_cf_acm_validation : name => values[0] },
  )

  zone_id = cloudflare_zone.caves_app.id
  name    = each.key
  type    = "CNAME"
  ttl     = local.default_ttl
  content = each.value
  proxied = false
}

resource "cloudflare_dns_record" "caves_app_mx" {
  for_each = local.caves_app_cf_mx

  zone_id  = cloudflare_zone.caves_app.id
  name     = each.value.name
  type     = "MX"
  ttl      = local.default_ttl
  content  = each.value.content
  priority = each.value.priority
  proxied  = false
}

resource "cloudflare_dns_record" "caves_app_txt" {
  for_each = local.caves_app_cf_txts

  zone_id = cloudflare_zone.caves_app.id
  name    = each.key
  type    = "TXT"
  ttl     = local.default_ttl
  content = "\"${each.value}\""
  proxied = false
}
