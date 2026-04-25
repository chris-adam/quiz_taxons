from django.db import migrations, models


def set_existing_records_to_nature(apps, schema_editor):
    Taxon = apps.get_model("taxons", "Taxon")
    Taxon.objects.filter(dataset="").update(dataset="nature")


class Migration(migrations.Migration):

    dependencies = [
        ("taxons", "0003_taxon_category"),
    ]

    operations = [
        migrations.AddField(
            model_name="taxon",
            name="dataset",
            field=models.CharField(max_length=50, db_index=True, default=""),
        ),
        migrations.RunPython(
            set_existing_records_to_nature,
            migrations.RunPython.noop,
        ),
    ]
