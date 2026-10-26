from django.test import TestCase
from django.urls import reverse

from accounts.models import User

from .models import Feedback


class FeedbackTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_user('admin', 'admin@example.com', 'pw', role=User.Role.ADMIN)
        cls.alice = User.objects.create_user('alice', 'alice@example.com', 'pw')
        cls.bob = User.objects.create_user('bob', 'bob@example.com', 'pw')
        cls.alice_feedback = Feedback.objects.create(
            customer=cls.alice, rating=5, subject='Lovely staff', message='Very helpful.'
        )
        cls.bob_feedback = Feedback.objects.create(
            customer=cls.bob,
            rating=2,
            category=Feedback.Category.DELIVERY,
            subject='Late parcel',
            message='Arrived a week late.',
        )


class HomeTests(FeedbackTestCase):
    def test_anonymous_goes_to_login(self):
        self.assertRedirects(self.client.get(reverse('home')), reverse('accounts:login'))

    def test_customer_goes_to_own_feedback(self):
        self.client.force_login(self.alice)
        self.assertRedirects(self.client.get(reverse('home')), reverse('feedback:mine'))

    def test_admin_goes_to_dashboard(self):
        self.client.force_login(self.admin)
        self.assertRedirects(self.client.get(reverse('home')), reverse('feedback:dashboard'))


class AnonymousAccessTests(FeedbackTestCase):
    def test_pages_require_login(self):
        login_url = reverse('accounts:login')
        for url in [
            reverse('feedback:create'),
            reverse('feedback:mine'),
            reverse('feedback:dashboard'),
            reverse('feedback:detail', args=[self.alice_feedback.pk]),
        ]:
            with self.subTest(url=url):
                self.assertRedirects(self.client.get(url), f'{login_url}?next={url}')


class CustomerTests(FeedbackTestCase):
    def setUp(self):
        self.client.force_login(self.alice)

    def test_submit_feedback_is_owned_by_logged_in_customer(self):
        response = self.client.post(reverse('feedback:create'), {
            'rating': 4,
            'category': Feedback.Category.PRODUCT,
            'subject': 'Nice app',
            'message': 'Easy to use.',
            'customer': self.bob.pk,  # must be ignored
            'status': Feedback.Status.RESOLVED,  # must be ignored
        })

        self.assertRedirects(response, reverse('feedback:mine'))
        feedback = Feedback.objects.get(subject='Nice app')
        self.assertEqual(feedback.customer, self.alice)
        self.assertEqual(feedback.status, Feedback.Status.NEW)

    def test_rating_is_required(self):
        response = self.client.post(reverse('feedback:create'), {
            'category': Feedback.Category.PRODUCT, 'subject': 'No rating', 'message': '...',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Feedback.objects.filter(subject='No rating').exists())

    def test_list_shows_only_own_feedback(self):
        response = self.client.get(reverse('feedback:mine'))
        self.assertContains(response, 'Lovely staff')
        self.assertNotContains(response, 'Late parcel')

    def test_can_view_own_feedback(self):
        response = self.client.get(reverse('feedback:detail', args=[self.alice_feedback.pk]))
        self.assertContains(response, 'Very helpful.')

    def test_cannot_view_other_customers_feedback(self):
        response = self.client.get(reverse('feedback:detail', args=[self.bob_feedback.pk]))
        self.assertEqual(response.status_code, 404)

    def test_cannot_access_dashboard(self):
        self.assertEqual(self.client.get(reverse('feedback:dashboard')).status_code, 403)

    def test_cannot_review_feedback(self):
        response = self.client.post(
            reverse('feedback:review', args=[self.alice_feedback.pk]),
            {'status': Feedback.Status.RESOLVED, 'admin_response': 'Self-approved'},
        )
        self.assertEqual(response.status_code, 403)
        self.alice_feedback.refresh_from_db()
        self.assertEqual(self.alice_feedback.status, Feedback.Status.NEW)

    def test_cannot_delete_feedback(self):
        response = self.client.post(reverse('feedback:delete', args=[self.alice_feedback.pk]))
        self.assertEqual(response.status_code, 403)
        self.assertTrue(Feedback.objects.filter(pk=self.alice_feedback.pk).exists())


class AdminTests(FeedbackTestCase):
    def setUp(self):
        self.client.force_login(self.admin)

    def test_dashboard_lists_all_feedback(self):
        response = self.client.get(reverse('feedback:dashboard'))
        self.assertContains(response, 'Lovely staff')
        self.assertContains(response, 'Late parcel')
        self.assertEqual(response.context['stats']['total'], 2)

    def test_dashboard_filters(self):
        cases = [
            ({'category': Feedback.Category.DELIVERY}, 'Late parcel', 'Lovely staff'),
            ({'rating': 5}, 'Lovely staff', 'Late parcel'),
            ({'q': 'bob@example'}, 'Late parcel', 'Lovely staff'),
        ]
        for params, included, excluded in cases:
            with self.subTest(params=params):
                response = self.client.get(reverse('feedback:dashboard'), params)
                self.assertContains(response, included)
                self.assertNotContains(response, excluded)

    def test_can_view_any_feedback(self):
        response = self.client.get(reverse('feedback:detail', args=[self.bob_feedback.pk]))
        self.assertContains(response, 'Arrived a week late.')
        self.assertContains(response, 'bob@example.com')

    def test_review_updates_status_and_response(self):
        url = reverse('feedback:detail', args=[self.bob_feedback.pk])
        response = self.client.post(
            reverse('feedback:review', args=[self.bob_feedback.pk]),
            {'status': Feedback.Status.RESOLVED, 'admin_response': 'Sorry! Refund issued.'},
        )

        self.assertRedirects(response, url)
        self.bob_feedback.refresh_from_db()
        self.assertEqual(self.bob_feedback.status, Feedback.Status.RESOLVED)

        # The customer sees the reply.
        self.client.force_login(self.bob)
        self.assertContains(self.client.get(url), 'Sorry! Refund issued.')

    def test_delete(self):
        response = self.client.post(reverse('feedback:delete', args=[self.bob_feedback.pk]))
        self.assertRedirects(response, reverse('feedback:dashboard'))
        self.assertFalse(Feedback.objects.filter(pk=self.bob_feedback.pk).exists())

    def test_admin_cannot_submit_feedback(self):
        self.assertEqual(self.client.get(reverse('feedback:create')).status_code, 403)
