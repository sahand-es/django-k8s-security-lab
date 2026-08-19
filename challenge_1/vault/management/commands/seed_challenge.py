import hashlib
import os

from django.core.management.base import BaseCommand, CommandError

from vault.models import Queue, Ticket


class Command(BaseCommand):
    help = "Seed the support desk challenge from TEAM_FLAGS."

    def handle(self, *args, **options):
        raw = os.environ.get("TEAM_FLAGS", "")
        flags = [f.strip() for f in raw.split(",") if f.strip()]
        if len(flags) != 3:
            raise CommandError(
                "TEAM_FLAGS must be three comma-separated flag values, "
                "e.g. FLAG{a},FLAG{b},FLAG{c}"
            )
        flag1, flag2, flag3 = flags

        seed = raw
        hidden_id = 100000 + (int(hashlib.sha256(seed.encode()).hexdigest(), 16) % 800000)

        Ticket.objects.all().delete()
        Queue.objects.all().delete()

        queue = Queue.objects.create(
            external_id=4107,
            name="Support · L1",
            squad=os.environ.get("LAB_REGION", "local"),
            member_username="intern",
            dashboard_note=(
                "Level-1 support console. Assigned tickets for the intern rotation are listed "
                "here; P0 tickets handled by the on-call team are locked to staff."
            ),
        )
        Ticket.objects.create(
            external_id=1201,
            queue=queue,
            title="TICKET-1201 · the platform onboarding flow",
            summary="Customer cannot see deploy logs in the dashboard.",
            body=(
                "Onboarding request: a new customer cannot find the deploy logs panel in "
                "the platform. Reply with the docs link and confirm workspace access. Safe for "
                "normal intern preview."
            ),
            visible_in_frontend=True,
            staff_only=False,
        )
        Ticket.objects.create(
            external_id=hidden_id,
            queue=queue,
            title="TICKET-%d · P0 archive sync stalled" % hidden_id,
            summary=f"Executor-only. Handover codeword: {flag1}",
            body=(
                "P0 incident thread.\n\n"
                f"Handover shard: {flag2}\n\n"
                f"Staff escalate via the handover page for this ticket:\n"
                f"  /staff/handover/{hidden_id}/\n"
                "Reach it through the Back-to-dashboard hop:\n"
                f"  /back/?next=/staff/handover/{hidden_id}/"
            ),
            visible_in_frontend=False,
            staff_only=True,
            handoff_note=flag3,
        )

        self.stdout.write(self.style.SUCCESS("Seeded Support desk challenge data."))
