from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("taxons", "0004_taxon_dataset"),
    ]

    operations = [
        migrations.AddField(
            model_name="taxon",
            name="inaturalist_taxon_id",
            field=models.IntegerField(null=True, blank=True),
        ),
        migrations.AlterUniqueTogether(
            name="taxon",
            unique_together={("inaturalist_taxon_id", "dataset")},
        ),
    ]
