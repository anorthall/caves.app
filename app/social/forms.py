from django import forms
from django.db.models import Q
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.urls import reverse
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Div
from crispy_bootstrap5.bootstrap5 import FloatingField
from social.models import FriendRequest


User = get_user_model()


class AddFriendForm(forms.Form):
    """A form used to send a friend request to another user."""

    user = forms.CharField(
        label="Username or email address",
        max_length=150,
    )

    def __init__(self, request, *args, **kwargs):
        self.request = request
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = "post"
        self.helper.form_class = "mt-3"
        self.helper.form_show_errors = False
        self.helper.form_action = reverse("social:friend_add")
        self.helper.layout = Layout(
            Div(
                Div(
                    FloatingField("user"),
                    css_class="col-12 col-md-8",
                ),
                Div(
                    Submit("submit", "Add friend", css_class="h-100 w-100"),
                    css_class="col-12 col-md-4 mb-3",
                ),
                css_class="row",
            )
        )

    def clean_user(self):
        """Validate the user field and convert it to a User object"""
        user = self.cleaned_data["user"].strip().lower()
        try:
            user = User.objects.get(username=user)
        except User.DoesNotExist:
            try:
                user = User.objects.get(email=user)
            except User.DoesNotExist:
                raise ValidationError("User not found.")

        if user == self.request.user:
            raise ValidationError("You cannot add yourself as a friend.")

        if user in self.request.user.friends.all():
            raise ValidationError(f"{user.name} is already your friend.")

        sent_req = Q(user_from=self.request.user, user_to=user)
        recd_req = Q(user_from=user, user_to=self.request.user)
        if FriendRequest.objects.filter(sent_req | recd_req).exists():
            raise ValidationError(
                "A friend request already exists for this user. "
                "You may need to wait for them to accept it, or "
                "accept it yourself using the form below."
            )

        return user
