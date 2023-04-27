class AuthStateTemplateMixin:
    """Render a different template based on whether or not the user is authenticated"""

    template_suffix = ".html"

    def get_template_names(self):
        if self.request.user.is_authenticated:
            return [self.template_name + "_authenticated" + self.template_suffix]
        else:
            return [self.template_name + "_anonymous" + self.template_suffix]
