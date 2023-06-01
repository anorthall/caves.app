from crispy_bootstrap5.bootstrap5 import FloatingField
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Div, Fieldset, Layout, Submit
from django import forms
from django.contrib import auth
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
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
    def __init__(self, *args, **kwargs):
        super(PasswordChangeForm, self).__init__(*args, **kwargs)
        self.fields["new_password1"].help_text = ""
        self.fields["new_password2"].help_text = (
            "Your password can't be too similar to your other personal "
            "information, must contain at least 8 characters, cannot be entirely "
            "numeric and must not be a commonly used password."
        )
        self.helper = FormHelper()
        self.helper.form_method = "post"
        self.helper.form_class = "mw-35"
        self.helper.layout = Layout(
            Fieldset(
                "Change password",
                "old_password",
                "new_password1",
                "new_password2",
                Submit("submit", "Change password"),
            )
        )


class PasswordResetForm(auth.forms.PasswordResetForm):
    template_name = "_bs5_form.html"


class SetPasswordForm(auth.forms.SetPasswordForm):
    template_name = "_bs5_form.html"

    def __init__(self, *args, **kwargs):
        super(SetPasswordForm, self).__init__(*args, **kwargs)
        self.fields["new_password1"].help_text = ""
        self.fields["new_password2"].help_text = (
            "Your password can't be too similar to your other personal "
            "information, must contain at least 8 characters, cannot be entirely "
            "numeric and must not be a commonly used password."
        )


class VerifyEmailForm(forms.Form):
    verify_code = forms.CharField(
        label="Verification code", max_length=100, required=True
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = None
        self.email = None
        self.helper = FormHelper()
        self.helper.form_method = "post"
        self.helper.form_class = "mw-45 mt-4"
        self.helper.add_input(Submit("submit", "Verify email"))

    def clean_verify_code(self):
        verify_code = self.cleaned_data["verify_code"]
        user_pk, email = verify_token(verify_code)
        try:
            user = User.objects.get(pk=user_pk)
        except User.DoesNotExist:
            raise ValidationError(
                "Email verification code is not valid or has expired."
            )

        self.user = user
        self.email = email
        return verify_code


class ResendVerifyEmailForm(forms.Form):
    template_name = "_bs5_form.html"
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
        except User.DoesNotExist:
            return email

        if not user.is_active:
            self.user = user
        return email


class UserCreationForm(forms.ModelForm):
    password1 = forms.CharField(
        label="Password",
        widget=forms.PasswordInput,
        help_text=(
            "Your password can't be too similar to your other personal "
            "information, must contain at least 8 characters, cannot be entirely "
            "numeric and must not be a commonly used password."
        ),
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
        self.helper = FormHelper()
        self.helper.form_method = "post"
        self.helper.form_class = "mw-35"
        self.helper.add_input(
            Submit("submit", "Create account", css_class="w-100 btn-lg mt-3")
        )

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

    def clean_username(self):
        username = self.cleaned_data.get("username")
        if User.objects.filter(username__iexact=username).exists():
            raise ValidationError("Username already taken.")
        return username

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


class SettingsChangeForm(forms.ModelForm):
    class Meta:
        model = User
        fields = (
            "privacy",
            "units",
            "timezone",
            "private_notes",
            "public_statistics",
            "allow_friend_username",
            "allow_friend_email",
            "allow_comments",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = "post"
        self.helper.layout = Layout(
            Fieldset(
                "Account settings",
                Div(
                    Div("privacy", css_class="col"),
                    Div("units", css_class="col"),
                    Div("timezone", css_class="col"),
                    css_class="row row-cols-1 row-cols-xl-3",
                ),
                Div(
                    Div("private_notes", css_class="col"),
                    Div("public_statistics", css_class="col"),
                    Div("allow_friend_username", css_class="col"),
                    Div("allow_friend_email", css_class="col"),
                    Div("allow_comments", css_class="col"),
                    css_class="row row-cols-1 row-cols-lg-3 mt-4",
                ),
            ),
            Submit("submit", "Save changes", css_class="btn-lg w-100 mt-4"),
        )


class ProfileChangeForm(forms.ModelForm):
    class Meta:
        model = User
        fields = (
            "name",
            "username",
            "location",
            "country",
            "page_title",
            "bio",
            "clubs",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = "post"
        self.helper.layout = Layout(
            Fieldset(
                "Personal details",
                Div(
                    Div("name", css_class="col"),
                    Div("username", css_class="col"),
                    Div("location", css_class="col"),
                    Div("country", css_class="col"),
                    css_class="row row-cols-1 row-cols-lg-2",
                ),
            ),
            Fieldset(
                "Profile settings",
                Div(
                    Div("page_title", css_class="col"),
                    Div("bio", css_class="col"),
                    Div("clubs", css_class="col"),
                    css_class="row row-cols-1",
                ),
                css_class="mt-4",
            ),
            Submit("submit", "Save changes", css_class="btn-lg w-100 mt-4"),
        )


class UserChangeEmailForm(forms.Form):
    email = forms.EmailField(
        label="New email address",
        max_length=255,
        required=True,
        help_text=(
            "This email address will be verified before any change is "
            "stored on the system."
        ),
    )
    password = forms.CharField(
        label="Current password",
        required=True,
        widget=forms.PasswordInput(),
        help_text="For security reasons, please enter your existing password.",
    )

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        self.helper = FormHelper()
        self.helper.form_method = "post"
        self.helper.form_class = "mw-35"
        self.helper.layout = Layout(
            Fieldset(
                "Change email address",
                "email",
                "password",
                Submit("submit", "Update email"),
            )
        )

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
