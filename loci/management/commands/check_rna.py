from django.core.management.base import BaseCommand, CommandError
from django.db import connections
from django.db.utils import DatabaseError

from loci.models import Locus, LocusMember

DB_ALIAS = "rnacentral"


class Command(BaseCommand):
    help = "Check the connection to RNAcentral DB and read the tables used by /locus"

    def handle(self, *args, **options):
        conn = connections[DB_ALIAS]
        s = conn.settings_dict
        self.stdout.write(f"Connecting to {s['USER']}@{s['HOST']}:{s['PORT']}/{s['NAME']}")

        try:
            conn.ensure_connection()
        except DatabaseError as e:
            raise CommandError(f"Connection failed: {e}")
        self.stdout.write(self.style.SUCCESS("Connected"))

        failed = False
        for model in (Locus, LocusMember):
            table = model._meta.db_table
            try:
                row = model.objects.values().first()
            except DatabaseError as e:
                failed = True
                error = str(e).strip().splitlines()[0]
                self.stdout.write(self.style.ERROR(f"[FAIL] {table}: {error}"))
            else:
                self.stdout.write(self.style.SUCCESS(f"[OK]   {table}: first row = {row}"))

        if failed:
            raise CommandError("Some tables are not accessible")
        self.stdout.write(self.style.SUCCESS("All tables are accessible"))