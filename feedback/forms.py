from django import forms
from django.db.models import Q

from .models import Feedback


class FeedbackForm(forms.ModelForm):
    # Declared explicitly so the radio list has no empty "---------" choice.
    rating = forms.TypedChoiceField(
        choices=Feedback.Rating.choices,
        coerce=int,
        widget=forms.RadioSelect,
        label='How would you rate your experience?',
    )

    class Meta:
        model = Feedback
        fields = ('rating', 'category', 'subject', 'message')
        widgets = {
            'subject': forms.TextInput(attrs={'placeholder': 'Summarize your feedback in a few words'}),
            'message': forms.Textarea(attrs={'rows': 6, 'placeholder': 'What happened? What could we do better?'}),
        }


class FeedbackReviewForm(forms.ModelForm):
    class Meta:
        model = Feedback
        fields = ('status', 'admin_response')
        widgets = {
            'admin_response': forms.Textarea(attrs={'rows': 5, 'placeholder': 'The customer will see this reply.'}),
        }


class FeedbackFilterForm(forms.Form):
    q = forms.CharField(
        required=False,
        label='Search',
        widget=forms.SearchInput(attrs={'placeholder': 'Subject, message or customer'}),
    )
    status = forms.ChoiceField(required=False, choices=[('', 'All statuses'), *Feedback.Status.choices])
    category = forms.ChoiceField(required=False, choices=[('', 'All categories'), *Feedback.Category.choices])
    rating = forms.TypedChoiceField(
        required=False,
        coerce=int,
        empty_value=None,
        choices=[('', 'Any rating'), *Feedback.Rating.choices],
    )

    def filter(self, queryset):
        if not self.is_valid():
            return queryset
        data = self.cleaned_data
        if data['q']:
            queryset = queryset.filter(
                Q(subject__icontains=data['q'])
                | Q(message__icontains=data['q'])
                | Q(customer__username__icontains=data['q'])
                | Q(customer__email__icontains=data['q'])
            )
        if data['status']:
            queryset = queryset.filter(status=data['status'])
        if data['category']:
            queryset = queryset.filter(category=data['category'])
        if data['rating']:
            queryset = queryset.filter(rating=data['rating'])
        return queryset
