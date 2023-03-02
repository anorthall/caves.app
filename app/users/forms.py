from django import forms
from django.contrib import auth
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from .models import CavingUser


class PasswordChangeForm(auth.forms.PasswordChangeForm):
    template_name = "bs5_form.html"

    def __init__(self, *args, **kwargs):
        super(PasswordChangeForm, self).__init__(*args, **kwargs)
        self.fields["new_password1"].help_text = ""
        self.fields[
            "new_password2"
        ].help_text = "Your password can't be too similar to your other personal information, must contain at least 8 characters, cannot be entirely numeric and must not be a commonly used password."


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
            "bio",
            "timezone",
            "units",
            "is_active",
            "email_verified",
            "password",
        )


class UserChangeForm(forms.ModelForm):
    template_name = "bs5_form.html"

    class Meta:
        model = CavingUser
        fields = (
            "email",
            "first_name",
            "last_name",
            "username",
            "location",
            "bio",
            "timezone",
            "units",
        )
