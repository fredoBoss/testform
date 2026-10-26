from django.contrib import admin

from .models import Feedback


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ('subject', 'customer', 'category', 'rating', 'status', 'created_at')
    list_filter = ('status', 'category', 'rating')
    search_fields = ('subject', 'message', 'customer__username', 'customer__email')
    list_select_related = ('customer',)
