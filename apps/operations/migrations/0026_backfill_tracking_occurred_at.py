from django.db import migrations
from django.db.models import F


def backfill_occurred_at(apps, schema_editor):
    Tracking = apps.get_model("operations", "Tracking")

    # When occurred_at was introduced as a required field, Django populated
    # existing rows with the migration time. Existing history must retain the
    # original event time stored in timestamp.
    Tracking.objects.all().update(occurred_at=F("timestamp"))


class Migration(migrations.Migration):

    dependencies = [
        ("operations", "0025_alter_manifest_status"),
    ]

    operations = [
        migrations.RunPython(backfill_occurred_at, migrations.RunPython.noop),
    ]
