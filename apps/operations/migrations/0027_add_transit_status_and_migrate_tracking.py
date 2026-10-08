from django.db import migrations


def migrate_old_transit_tracking(apps, schema_editor):
    Tracking = apps.get_model("operations", "Tracking")
    # Before the separate status existed, TRANSFER was used for transit
    # tracking events. Manifest/shipment TRANSFER values remain Transfer
    # Location and are intentionally not changed here.
    Tracking.objects.filter(status="TRANSFER").update(status="TRANSIT")


class Migration(migrations.Migration):
    dependencies = [
        ("operations", "0026_backfill_tracking_occurred_at"),
    ]

    operations = [
        migrations.RunPython(migrate_old_transit_tracking, migrations.RunPython.noop),
    ]
