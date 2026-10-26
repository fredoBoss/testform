from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from accounts.models import User
from feedback.models import Feedback

# Local development only. These passwords are public; never run this against a real database.
DEMO_USERS = [
    {'username': 'admin', 'email': 'admin@example.com', 'password': 'admin-demo-123', 'role': User.Role.ADMIN},
    {
        'username': 'customer',
        'email': 'customer@example.com',
        'password': 'customer-demo-123',
        'role': User.Role.CUSTOMER,
        'first_name': 'Casey',
        'last_name': 'Rivera',
    },
    {'username': 'jordan', 'email': 'jordan@example.com', 'password': 'jordan-demo-123', 'role': User.Role.CUSTOMER},
]

DEMO_FEEDBACK = [
    {
        'customer': 'customer',
        'rating': 5,
        'category': Feedback.Category.SERVICE,
        'subject': 'Support sorted my issue fast',
        'message': 'I had a billing question and the support team answered within an hour. Really appreciated it.',
        'status': Feedback.Status.RESOLVED,
        'admin_response': 'Thanks for letting us know, Casey! We will pass this on to the team.',
    },
    {
        'customer': 'customer',
        'rating': 3,
        'category': Feedback.Category.WEBSITE,
        'subject': 'Checkout page is confusing',
        'message': 'It took me a while to find where to enter my discount code.',
    },
    {
        'customer': 'jordan',
        'rating': 2,
        'category': Feedback.Category.DELIVERY,
        'subject': 'Parcel arrived late',
        'message': 'My order was supposed to arrive Tuesday but came on Friday.',
        'status': Feedback.Status.IN_REVIEW,
    },
]


class Command(BaseCommand):
    help = 'Create demo admin/customer accounts and sample feedback for local development.'

    def handle(self, *args, **options):
        if not settings.DEBUG:
            raise CommandError('seed_demo only runs with DEBUG enabled.')

        users = {}
        for data in DEMO_USERS:
            data = data.copy()
            password = data.pop('password')
            user, created = User.objects.get_or_create(username=data['username'], defaults=data)
            if created:
                user.set_password(password)
                if user.is_admin:
                    user.is_staff = user.is_superuser = True  # also allow /admin/
                user.save()
            users[user.username] = user
            self.stdout.write(f"{'Created' if created else 'Exists '} {user.role:<8} {user.username}")

        for data in DEMO_FEEDBACK:
            data = {**data, 'customer': users[data['customer']]}
            Feedback.objects.get_or_create(customer=data['customer'], subject=data['subject'], defaults=data)

        self.stdout.write(self.style.SUCCESS(f'Demo data ready ({Feedback.objects.count()} feedback items).'))
