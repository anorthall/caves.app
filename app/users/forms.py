from crispy_bootstrap5.bootstrap5 import FloatingField
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Div, Layout, Submit
from django import forms
from django.contrib import auth
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db.models import Q
from django.urls import reverse

from .models import FriendRequest
from .verify import verify_token

User = get_user_model()


class AuthenticationForm(auth.forms.AuthenticationForm):
    def __init__(self, request, *args, **kwargs):
        self.request = request
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = "post"
        self.helper.form_class = "mb-4"
        self.helper.form_show_errors = False
        self.helper.layout = Layout(
            Div(
                Div(
                    FloatingField("username"),
                    css_class="col-12",
                ),
                Div(
                    FloatingField("password"),
                    css_class="col-12",
                ),
                Div(
                    Submit("submit", "Submit", css_class="btn-lg h-100 w-100"),
                    css_class="col-12",
                ),
                css_class="row",
            )
        )


class PasswordChangeForm(auth.forms.PasswordChangeForm):
    template_name = "forms/bs5_form.html"

    def __init__(self, *args, **kwargs):
        super(PasswordChangeForm, self).__init__(*args, **kwargs)
        self.fields["new_password1"].help_text = ""
        self.fields[
            "new_password2"
        ].help_text = "Your password can't be too similar to your other personal "
        "information, must contain at least 8 characters, cannot be entirely numeric "
        "and must not be a commonly used password."


class PasswordResetForm(auth.forms.PasswordResetForm):
    template_name = "forms/bs5_form.html"


class SetPasswordForm(auth.forms.SetPasswordForm):
    template_name = "forms/bs5_form.html"

    def __init__(self, *args, **kwargs):
        super(SetPasswordForm, self).__init__(*args, **kwargs)
        self.fields["new_password1"].help_text = ""
        self.fields[
            "new_password2"
        ].help_text = "Your password can't be too similar to your other personal "
        "information, must contain at least 8 characters, cannot be entirely numeric "
        "and must not be a commonly used password."


class VerifyEmailForm(forms.Form):
    template_name = "forms/bs5_form.html"
    verify_code = forms.CharField(
        label="Verification code", max_length=100, required=True
    )

    def __init__(self, *args, **kwargs):
        self.user = None
        self.email = None
        super().__init__(*args, **kwargs)

    def clean_verify_code(self):
        verify_code = self.cleaned_data["verify_code"]
        user_pk, email = verify_token(verify_code)
        try:
            user = User.objects.get(pk=user_pk)
        except ObjectDoesNotExist:
            raise ValidationError(
                "Email verification code is not valid or has expired."
            )

        self.user = user
        self.email = email
        return verify_code


class ResendVerifyEmailForm(forms.Form):
    template_name = "forms/bs5_form.html"
    email = forms.EmailField(
        label="Email address",
        max_length=255,
        required=True,
        help_text="The email address you signed up with.",
    )

    def __init__(self, *args, **kwargs):
        self.user = None
        super().__init__(*args, **kwargs)

    def clean_email(self):
        # Set self.user only if the email belongs to an inactive account
        email = self.cleaned_data["email"]
        try:
            user = User.objects.get(email__exact=email)
        except ObjectDoesNotExist:
            return email

        if not user.is_active:
            self.user = user
        return email


class UserCreationForm(forms.ModelForm):
    template_name = "forms/bs5_form.html"
    password1 = forms.CharField(
        label="Password",
        widget=forms.PasswordInput,
        help_text="Your password can't be too similar to your other personal "
        "information, must contain at least 8 characters, cannot be entirely numeric "
        "and must not be a commonly used password.",
        required=True,
    )
    password2 = forms.CharField(
        label="Confirm password",
        widget=forms.PasswordInput,
        help_text="Enter the same password as before, for verification.",
        required=True,
    )

    class Meta:
        model = User
        fields = ("name", "email", "username")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["name"].widget.attrs["autofocus"] = True
        self.fields["name"].widget.attrs["autocomplete"] = "name"
        self.fields["email"].widget.attrs["autocomplete"] = "email"
        self.fields["name"].initial = None

    def clean_password2(self):
        # Check that the two password entries match
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            error = "Passwords do not match."
            self.add_error("password1", error)
            self.add_error("password2", error)

        try:
            validate_password(password2)
        except ValidationError as error:
            self.add_error("password1", error)
            self.add_error("password2", error)

        return password2

    def save(self, commit=True):
        # Save the provided password in hashed format
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])

        if commit:
            user.save()

        return user


class UserAdminChangeForm(forms.ModelForm):
    password = ReadOnlyPasswordHashField()

    class Meta:
        model = User
        fields = (
            "email",
            "username",
            "name",
            "is_active",
            "password",
        )


class UserChangeForm(forms.ModelForm):
    template_name = "forms/user_change_form.html"
    email = forms.EmailField(
        disabled=True,
        help_text="Use the change email page to update your email address.",
    )

    class Meta:
        model = User
        fields = (
            "email",
            "username",
            "name",
        )


class ProfileChangeForm(forms.ModelForm):
    template_name = "forms/profile_change_form.html"

    class Meta:
        model = User
        fields = (
            "location",
            "country",
            "clubs",
            "page_title",
            "bio",
        )


class SettingsChangeForm(forms.ModelForm):
    template_name = "forms/settings_change_form.html"

    class Meta:
        model = User
        fields = (
            "privacy",
            "private_notes",
            "units",
            "timezone",
            "public_statistics",
            "allow_friend_username",
            "allow_friend_email",
            "allow_comments",
        )


class UserChangeEmailForm(forms.Form):
    template_name = "forms/bs5_form.html"
    email = forms.EmailField(
        label="New email address",
        max_length=255,
        required=True,
        help_text="This email address will be verified before any change is "
        "stored on the system.",
    )
    password = forms.CharField(
        label="Current password",
        required=True,
        widget=forms.PasswordInput(),
        help_text="For security reasons, please enter your existing password.",
    )

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_password(self):
        """Check the user entered their password correctly"""
        password = self.cleaned_data["password"]
        if not self.user.check_password(password):
            raise ValidationError("The password you have entered is not correct.")
        return password

    def clean_email(self):
        """Check if the email is already in use"""
        email = self.cleaned_data["email"]
        if User.objects.filter(email=email).exists():
            raise ValidationError("That email is already in use.")
        return email


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
        self.helper.form_action = reverse("users:friend_add")
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
        user_input = user  # For error messages

        try:
            user = User.objects.get(username=user)
            if not user.allow_friend_username:
                raise User.DoesNotExist
        except User.DoesNotExist:
            try:
                user = User.objects.get(email=user)
                if not user.allow_friend_email:
                    raise User.DoesNotExist
            except User.DoesNotExist:
                raise ValidationError(
                    f"Could not find a user with the identifier '{user_input}'."
                )

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
