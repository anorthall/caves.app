from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from django import forms


class TripExportForm(forms.Form):
    FORMAT_CHOICES = (
        ("csv", "CSV (Google Sheets/Excel)"),
        ("json", "JSON (JavaScript Object Notation)"),
    )
    format = forms.ChoiceField(choices=FORMAT_CHOICES)
    # email = forms.BooleanField(  # TODO: Implement this
    #     label="Email me the data",
    #     required=False,
    #     help_text="Send the export to your email address as well as downloading it",
    # )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.add_input(
            Submit("submit", "Export data", css_class="btn btn-primary")
        )
        self.helper.form_method = "post"
