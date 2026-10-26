from django.conf import settings
from django.db import models
from django.urls import reverse


class FeedbackQuerySet(models.QuerySet):
    def visible_to(self, user):
        """Admins see everything; customers see only their own feedback."""
        if not user.is_authenticated:
            return self.none()
        if user.is_admin:
            return self
        return self.filter(customer=user)


class Feedback(models.Model):
    class Category(models.TextChoices):
        PRODUCT = 'product', 'Product'
        SERVICE = 'service', 'Customer service'
        DELIVERY = 'delivery', 'Delivery'
        WEBSITE = 'website', 'Website or app'
        OTHER = 'other', 'Other'

    class Rating(models.IntegerChoices):
        TERRIBLE = 1, 'Terrible'
        POOR = 2, 'Poor'
        OKAY = 3, 'Okay'
        GOOD = 4, 'Good'
        EXCELLENT = 5, 'Excellent'

    class Status(models.TextChoices):
        NEW = 'new', 'New'
        IN_REVIEW = 'in_review', 'In review'
        RESOLVED = 'resolved', 'Resolved'

    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='feedback')
    category = models.CharField(max_length=20, choices=Category.choices, default=Category.PRODUCT)
    rating = models.PositiveSmallIntegerField(choices=Rating.choices)
    subject = models.CharField(max_length=120)
    message = models.TextField(max_length=5000)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.NEW)
    admin_response = models.TextField('response', blank=True, max_length=5000)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = FeedbackQuerySet.as_manager()

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'feedback'

    def __str__(self):
        return self.subject

    def get_absolute_url(self):
        return reverse('feedback:detail', args=[self.pk])
