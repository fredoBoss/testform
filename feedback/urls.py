from django.urls import path

from . import views

app_name = 'feedback'

urlpatterns = [
    path('new/', views.FeedbackCreateView.as_view(), name='create'),
    path('mine/', views.MyFeedbackListView.as_view(), name='mine'),
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    path('<int:pk>/', views.FeedbackDetailView.as_view(), name='detail'),
    path('<int:pk>/review/', views.FeedbackReviewView.as_view(), name='review'),
    path('<int:pk>/delete/', views.FeedbackDeleteView.as_view(), name='delete'),
]
