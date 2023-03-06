from django import forms
from django.contrib import auth
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from .models import CavingUser
from .verify import verify_token


class PasswordChangeForm(auth.forms.PasswordChangeForm):
    template_name = "bs5_form.html"

    def __init__(self, *args, **kwargs):
        super(PasswordChangeForm, self).__init__(*args, **kwargs)
        self.fields["new_password1"].help_text = ""
        self.fields[
            "new_password2"
        ].help_text = "Your password can't be too similar to your other personal information, must contain at least 8 characters, cannot be entirely numeric and must not be a commonly used password."


class VerifyEmailForm(forms.Form):
    template_name = "bs5_form.html"
    verify_code = forms.CharField(
        label="Verification code", max_length=100, required=True
    )

    def __init__(self, *args, **kwargs):
        self.user = None
        self.email = None
        super().__init__(*args, **kwargs)

    def clean_verify_code(self):
        verify_code = self.cleaned_data["verify_code"]
        # Decode the user ID and email from the hash
        user_pk, email = verify_token(verify_code)
        # Check we have a user with the decoded email
        try:
            user = auth.get_user_model().objects.get(pk=user_pk)
        except ObjectDoesNotExist:
            raise ValidationError(
                "Email verification code is not valid or has expired."
            )

        # Save the user and email
        self.user = user
        self.email = email
        return verify_code


class LoginForm(forms.Form):
    template_name = "login_form.html"
    email = forms.EmailField(label="Email address", max_length=255, required=True)
    password = forms.CharField(
        label="Password", required=True, widget=forms.PasswordInput()
    )


class UserCreationForm(forms.ModelForm):
    template_name = "bs5_form.html"
    password1 = forms.CharField(
        label="Password",
        widget=forms.PasswordInput,
        help_text="Your password can't be too similar to your other personal information, must contain at least 8 characters, cannot be entirely numeric and must not be a commonly used password.",
    )
    password2 = forms.CharField(
        label="Confirm password",
        widget=forms.PasswordInput,
        help_text="Enter the same password as before, for verification.",
    )

    class Meta:
        model = CavingUser
        fields = ("first_name", "last_name", "email", "username")

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
        model = CavingUser
        fields = (
            "email",
            "first_name",
            "last_name",
            "location",
            "club",
            "bio",
            "timezone",
            "units",
            "is_active",
            "password",
        )


class UserChangeForm(forms.ModelForm):
    template_name = "bs5_form.html"
    email = forms.EmailField(disabled=True)  # Use specific form

    class Meta:
        model = CavingUser
        fields = (
            "email",
            "first_name",
            "last_name",
            "username",
            "location",
            "club",
            "bio",
            "timezone",
            "units",
        )


class UserChangeEmailForm(forms.Form):
    template_name = "bs5_form.html"
    email = forms.EmailField(
        label="New email address",
        max_length=255,
        required=True,
        help_text="This email address will be verified before any change is stored on the system.",
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
        if auth.get_user_model().objects.filter(email=email).exists():
            raise ValidationError("That email is already in use.")
        return email
