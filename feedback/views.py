from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Avg, Count, Q
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from accounts.mixins import AdminRequiredMixin, CustomerRequiredMixin

from .forms import FeedbackFilterForm, FeedbackForm, FeedbackReviewForm
from .models import Feedback


def home(request):
    if not request.user.is_authenticated:
        return redirect('accounts:login')
    if request.user.is_admin:
        return redirect('feedback:dashboard')
    return redirect('feedback:mine')


class FeedbackCreateView(CustomerRequiredMixin, SuccessMessageMixin, CreateView):
    model = Feedback
    form_class = FeedbackForm
    success_url = reverse_lazy('feedback:mine')
    success_message = 'Thanks! Your feedback has been sent.'

    def form_valid(self, form):
        form.instance.customer = self.request.user
        return super().form_valid(form)


class MyFeedbackListView(CustomerRequiredMixin, ListView):
    template_name = 'feedback/feedback_list.html'
    context_object_name = 'feedback_list'
    paginate_by = 10

    def get_queryset(self):
        return Feedback.objects.visible_to(self.request.user)


class FeedbackDetailView(LoginRequiredMixin, DetailView):
    context_object_name = 'feedback'

    def get_queryset(self):
        # Another customer's feedback 404s rather than 403s, so its existence isn't revealed.
        return Feedback.objects.visible_to(self.request.user).select_related('customer')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_admin:
            context['form'] = FeedbackReviewForm(instance=self.object)
        return context


class FeedbackReviewView(AdminRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Feedback
    form_class = FeedbackReviewForm
    # Invalid submissions re-render the detail page with the bound form.
    template_name = 'feedback/feedback_detail.html'
    context_object_name = 'feedback'
    http_method_names = ['post']
    success_message = 'Feedback updated.'


class FeedbackDeleteView(AdminRequiredMixin, SuccessMessageMixin, DeleteView):
    model = Feedback
    context_object_name = 'feedback'
    success_url = reverse_lazy('feedback:dashboard')
    success_message = 'Feedback deleted.'


class DashboardView(AdminRequiredMixin, ListView):
    template_name = 'feedback/dashboard.html'
    context_object_name = 'feedback_list'
    paginate_by = 20

    def get_queryset(self):
        self.filter_form = FeedbackFilterForm(self.request.GET or None)
        return self.filter_form.filter(Feedback.objects.select_related('customer'))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter_form'] = self.filter_form
        context['stats'] = Feedback.objects.aggregate(
            total=Count('id'),
            new=Count('id', filter=Q(status=Feedback.Status.NEW)),
            in_review=Count('id', filter=Q(status=Feedback.Status.IN_REVIEW)),
            resolved=Count('id', filter=Q(status=Feedback.Status.RESOLVED)),
            avg_rating=Avg('rating'),
        )
        return context
