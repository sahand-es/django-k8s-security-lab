import os
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Seed the on-call shadow challenge from TEAM_FLAGS."

    def handle(self, *args, **options):
        raw = os.environ.get("TEAM_FLAGS", "")
        flags = [f.strip() for f in raw.split(",") if f.strip()]
        if len(flags) != 2:
            raise CommandError(
                "TEAM_FLAGS must be two comma-separated flag values, "
                "e.g. FLAG{rce_flag},FLAG{ssrf_flag}"
            )
        flag1, flag2 = flags

        flag_path = Path(settings.FLAG_PATH)
        flag_path.parent.mkdir(parents=True, exist_ok=True)
        if not flag_path.exists():
            flag_path.write_text(flag1 + "\n", encoding="utf-8")
            flag_path.chmod(0o600)

        self.stdout.write(
            self.style.SUCCESS("Seeded on-call shadow data.")
        )
