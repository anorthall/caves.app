from django import forms


class LoginForm(forms.Form):
    template_name = "login_form.html"
    email = forms.EmailField(label="Email address", max_length=255, required=True)
    password = forms.CharField(
        label="Password", required=True, widget=forms.PasswordInput()
    )
