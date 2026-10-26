from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin


class AdminRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Anonymous users are sent to the login page; logged-in non-admins get a 403."""

    def test_func(self):
        return self.request.user.is_admin


class CustomerRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Anonymous users are sent to the login page; logged-in non-customers get a 403."""

    def test_func(self):
        return self.request.user.is_customer
