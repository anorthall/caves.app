from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.urls import reverse

from .models import Comment

User = get_user_model()


class CommentForm(forms.Form):
    content = forms.CharField(
        help_text="Your comment will be visible to anyone who can view this page.",
        widget=forms.Textarea(attrs={"rows": 4}),
    )

    def __init__(self, request, trip, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.request = request
        self.trip = trip

        self.helper = FormHelper()
        self.helper.form_method = "post"
        self.helper.form_class = ""
        self.helper.form_show_errors = False
        self.helper.form_show_labels = False
        self.helper.form_action = reverse("comments:add", kwargs={"uuid": trip.uuid})
        self.helper.add_input(Submit("submit", "Add comment"))

    def clean_content(self) -> str:
        content = self.cleaned_data.get("content")
        if len(content) > 2000:
            raise ValidationError(
                "Your comment must be less than 2000 characters long."
            )
        return content

    def clean(self):
        if not self.trip.is_viewable_by(self.request.user):
            raise ValidationError("You are not allowed to comment on that item.")

        if not self.trip.user.allow_comments:
            raise ValidationError("Comments are not allowed on that item.")

        return self.cleaned_data

    def save(self, commit=True) -> Comment:
        content = self.cleaned_data.get("content")
        new = Comment.objects.create(
            content=content, trip=self.trip, author=self.request.user
        )
        if commit:
            new.save()
        return new
