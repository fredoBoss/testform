from django.test import TestCase
from django.urls import reverse

from .models import User

PASSWORD = 'a-Strong-passw0rd!'


def signup_data(**overrides):
    return {
        'username': 'alice',
        'email': 'alice@example.com',
        'first_name': 'Alice',
        'last_name': 'Ng',
        'password1': PASSWORD,
        'password2': PASSWORD,
        **overrides,
    }


class SignUpTests(TestCase):
    def test_signup_creates_customer_and_logs_in(self):
        response = self.client.post(reverse('accounts:signup'), signup_data())

        self.assertRedirects(response, reverse('home'), fetch_redirect_response=False)
        user = User.objects.get(username='alice')
        self.assertEqual(user.role, User.Role.CUSTOMER)
        self.assertEqual(int(self.client.session['_auth_user_id']), user.pk)

    def test_signup_ignores_posted_role(self):
        self.client.post(reverse('accounts:signup'), signup_data(role=User.Role.ADMIN))

        self.assertEqual(User.objects.get(username='alice').role, User.Role.CUSTOMER)

    def test_email_must_be_unique(self):
        User.objects.create_user('existing', 'alice@example.com', PASSWORD)

        response = self.client.post(reverse('accounts:signup'), signup_data())

        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username='alice').exists())

    def test_logged_in_user_is_redirected_away_from_signup(self):
        self.client.force_login(User.objects.create_user('bob', 'bob@example.com', PASSWORD))

        response = self.client.get(reverse('accounts:signup'))

        self.assertRedirects(response, reverse('home'), fetch_redirect_response=False)


class LoginTests(TestCase):
    def test_login_and_logout(self):
        User.objects.create_user('bob', 'bob@example.com', PASSWORD)

        response = self.client.post(reverse('accounts:login'), {'username': 'bob', 'password': PASSWORD})
        self.assertRedirects(response, reverse('home'), fetch_redirect_response=False)

        response = self.client.post(reverse('accounts:logout'))
        self.assertRedirects(response, reverse('accounts:login'))
        self.assertNotIn('_auth_user_id', self.client.session)


class RoleTests(TestCase):
    def test_superuser_is_admin(self):
        user = User.objects.create_superuser('root', 'root@example.com', PASSWORD)
        self.assertTrue(user.is_admin)

    def test_regular_user_is_customer(self):
        user = User.objects.create_user('bob', 'bob@example.com', PASSWORD)
        self.assertTrue(user.is_customer)
        self.assertFalse(user.is_admin)


class UserManagementTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_user('admin', 'admin@example.com', PASSWORD, role=User.Role.ADMIN)
        cls.customer = User.objects.create_user('carol', 'carol@example.com', PASSWORD)

    def test_anonymous_is_redirected_to_login(self):
        response = self.client.get(reverse('accounts:users'))
        self.assertRedirects(response, f"{reverse('accounts:login')}?next={reverse('accounts:users')}")

    def test_customer_cannot_list_users(self):
        self.client.force_login(self.customer)
        self.assertEqual(self.client.get(reverse('accounts:users')).status_code, 403)

    def test_admin_can_list_users(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse('accounts:users'))
        self.assertContains(response, 'carol@example.com')

    def test_admin_can_create_admin(self):
        self.client.force_login(self.admin)

        response = self.client.post(
            reverse('accounts:create-admin'), signup_data(username='dave', email='dave@example.com')
        )

        self.assertRedirects(response, reverse('accounts:users'))
        self.assertEqual(User.objects.get(username='dave').role, User.Role.ADMIN)

    def test_customer_cannot_create_admin(self):
        self.client.force_login(self.customer)

        response = self.client.post(
            reverse('accounts:create-admin'), signup_data(username='dave', email='dave@example.com')
        )

        self.assertEqual(response.status_code, 403)
        self.assertFalse(User.objects.filter(username='dave').exists())
