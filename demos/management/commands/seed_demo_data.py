from django.core.management.base import BaseCommand

from demos.models import Account, Document, Product


class Command(BaseCommand):
    help = "Seed local-only data for the Part 1 and Part 2 security demos."

    def handle(self, *args, **options):
        Product.objects.all().delete()
        Account.objects.all().delete()
        Document.objects.all().delete()

        Product.objects.bulk_create(
            [
                Product(id=1, name="Team Alpha Roadmap", owner="alice", description="Private planning notes"),
                Product(id=2, name="Public Status Page", owner="alice", description="Safe public status summary"),
                Product(id=3, name="Team Beta Payroll", owner="bob", description="Private finance export"),
            ]
        )
        Account.objects.create(id=1, owner="alice", balance=1000)
        Document.objects.bulk_create(
            [
                Document(id=1, title="Alice Project Plan", owner="alice", body="Allowed for Alice"),
                Document(id=2, title="Bob Incident Notes", owner="bob", body="Not owned by Alice"),
            ]
        )

        self.stdout.write(self.style.SUCCESS("Seeded demo data."))
