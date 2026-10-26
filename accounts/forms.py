from django.contrib.auth.forms import UserCreationForm

from .models import User


class SignUpForm(UserCreationForm):
    """Public sign-up. The role is fixed by the form class, never taken from POST data."""

    role = User.Role.CUSTOMER

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email', 'first_name', 'last_name')

    def save(self, commit=True):
        self.instance.role = self.role
        return super().save(commit)


class AdminCreationForm(SignUpForm):
    """Used by an existing admin to create another admin account."""

    role = User.Role.ADMIN
