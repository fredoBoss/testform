from django.contrib.auth import login
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Count
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView

from .forms import AdminCreationForm, SignUpForm
from .mixins import AdminRequiredMixin
from .models import User


class SignUpView(SuccessMessageMixin, CreateView):
    form_class = SignUpForm
    template_name = 'accounts/signup.html'
    success_url = reverse_lazy('home')
    success_message = 'Welcome, %(username)s! Your account is ready.'

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('home')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        response = super().form_valid(form)
        login(self.request, self.object)
        return response


class UserListView(AdminRequiredMixin, ListView):
    template_name = 'accounts/user_list.html'
    context_object_name = 'users'
    paginate_by = 25

    def get_queryset(self):
        return User.objects.annotate(feedback_count=Count('feedback')).order_by('role', 'username')


class AdminCreateView(AdminRequiredMixin, SuccessMessageMixin, CreateView):
    form_class = AdminCreationForm
    template_name = 'accounts/admin_form.html'
    success_url = reverse_lazy('accounts:users')
    success_message = 'Admin account "%(username)s" created.'
