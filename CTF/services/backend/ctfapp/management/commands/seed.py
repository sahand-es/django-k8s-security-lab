import os

from django.core.management.base import BaseCommand

from ctfapp.models import Org, Report, User


class Command(BaseCommand):
    help = "Seed orgs, users, and reports"

    def handle(self, *args, **options):
        org_a, _ = Org.objects.get_or_create(pk=1, defaults={"name": "Acme Corp"})
        org_b, _ = Org.objects.get_or_create(pk=2, defaults={"name": "Globex Inc"})

        acme, _ = User.objects.get_or_create(
            username="acmeuser", defaults={"email": "acme@example.com"}
        )
        acme.org = org_a
        acme.set_password("Passw0rd!")
        acme.save()

        globex, _ = User.objects.get_or_create(
            username="globexuser", defaults={"email": "globex@example.com"}
        )
        globex.org = org_b
        globex.set_password("Passw0rd!")
        globex.save()

        Report.objects.get_or_create(
            org=org_a,
            title="Q3 Financial Summary",
            defaults={"secret_note": "Decoy: nothing interesting here."},
        )
        Report.objects.get_or_create(
            org=org_b,
            title="Globex Internal Audit",
            defaults={"secret_note": os.environ.get("FLAG_F5", "")},
        )

        self.stdout.write(self.style.SUCCESS("Seed complete"))
