import os

from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q

from accounts.models import User

ENV_VARS = ('DJANGO_SUPERUSER_USERNAME', 'DJANGO_SUPERUSER_EMAIL', 'DJANGO_SUPERUSER_PASSWORD')


class Command(BaseCommand):
    help = (
        'Create the first admin from the DJANGO_SUPERUSER_USERNAME, DJANGO_SUPERUSER_EMAIL and '
        'DJANGO_SUPERUSER_PASSWORD environment variables. Does nothing once any admin exists, or '
        'while the variables are unset. Run by the Vercel production build (vercel.json).'
    )

    def handle(self, *args, **options):
        if User.objects.filter(role=User.Role.ADMIN).exists():
            self.stdout.write('An admin already exists; nothing to do.')
            return

        username, email, password = (os.environ.get(name, '') for name in ENV_VARS)
        if not (username and email and password):
            self.stdout.write(f'No admin yet. Set {", ".join(ENV_VARS)} to create one.')
            return

        if User.objects.filter(Q(username__iexact=username) | Q(email__iexact=email)).exists():
            raise CommandError('DJANGO_SUPERUSER_USERNAME or DJANGO_SUPERUSER_EMAIL is already used by another account.')
        try:
            validate_password(password, User(username=username, email=email))
        except ValidationError as error:
            raise CommandError('DJANGO_SUPERUSER_PASSWORD was rejected: ' + ' '.join(error.messages))

        User.objects.create_superuser(username, email, password)
        self.stdout.write(self.style.SUCCESS(f'Created admin "{username}".'))
