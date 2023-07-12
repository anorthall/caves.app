from typing import Union

from attrs import define, field
from django.conf import settings
from django.core.mail import send_mail
from django.template.exceptions import TemplateDoesNotExist
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from users.models import CavingUser as User


@define
class Email:
    to: Union[list[str], str, User]
    context: dict
    template_name: str = field(init=False)
    required_context: list[str] = field(init=False)
    from_email: str = settings.DEFAULT_FROM_EMAIL

    def send(self) -> int:
        self._check_required_context_exists()

        # Add SITE_ROOT to context
        self.context["SITE_ROOT"] = settings.SITE_ROOT

        # TODO: use mjml to generate html email templates
        subject_template = f"emails/{self.template_name}_subject.txt"
        plain_template = f"emails/{self.template_name}.txt"
        html_template = f"emails/{self.template_name}.html"

        subject = render_to_string(subject_template, context=self.context)
        subject = "".join(subject.splitlines())  # subject must not contain newlines

        html_template = render_to_string(html_template, context=self.context)

        try:
            plain_template = render_to_string(plain_template, context=self.context)
        except TemplateDoesNotExist:
            plain_template = strip_tags(html_template)

        if isinstance(self.to, User):
            recipient_list = [self.to.email]
        elif isinstance(self.to, str):
            recipient_list = [self.to]
        else:
            recipient_list = self.to

        return send_mail(
            subject=subject,
            message=plain_template,
            html_message=html_template,
            from_email=self.from_email,
            recipient_list=recipient_list,
        )

    def _check_required_context_exists(self):
        for key in self.required_context:
            if key not in self.context:
                raise KeyError(f"Missing required context key: {key}")


class NewUserVerificationEmail(Email):
    template_name = "verify_new_account"
    required_context = ["name", "verify_url", "verify_code"]


class EmailChangeVerificationEmail(Email):
    template_name = "verify_email_change"
    required_context = ["name", "verify_url", "verify_code"]


class EmailChangeNotificationEmail(Email):
    template_name = "notify_of_email_change"
    required_context = ["name", "old_email", "new_email"]


class FriendRequestReceivedEmail(Email):
    template_name = "friend_request_received"
    required_context = ["name", "requester_name", "url"]


class FriendRequestAcceptedEmail(Email):
    template_name = "friend_request_accepted"
    required_context = ["name", "accepter_name", "url"]


class NewCommentEmail(Email):
    template_name = "new_comment"
    required_context = ["name", "commenter_name", "trip", "comment_content"]
