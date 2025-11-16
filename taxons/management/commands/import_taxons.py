import csv

import pdfplumber
from django.core.management.base import BaseCommand

from taxons.models import Taxon


class Command(BaseCommand):
    help = "Import taxons from CSV file"

    def add_arguments(self, parser):
        parser.add_argument("--file", type=str, default="taxons.pdf", help="Path to the PDF file (default: taxons.pdf)")

    def extract_pdf_to_csv(self, path):
        hdrs = [
            (
                "Règne",
                "Embranchement (Sous-embranchement)",
                "Classe",
                "Ordre (Sous-ordre)",
                "Famille",
                "Genre",
                "Espèce",
                "Nom vernaculaire",
                "Partie/état/indice à reconnaitre",
            )
        ]
        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                for tb in page.extract_tables():
                    for sub_tb in tb:
                        regne = sub_tb[0]
                        nom_vernaculaire = sub_tb[-2]
                        if regne != "Règne" and nom_vernaculaire:
                            hdrs.append(
                                tuple(
                                    [
                                        (
                                            str(cell.strip().replace("-\n", "").replace("\n", " "))
                                            if cell and cell != "-"
                                            else None
                                        )
                                        for cell in sub_tb
                                    ]
                                )
                            )

        with open("taxons.csv", "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerows(hdrs)

    def handle(self, *args, **options):
        file_path = options["file"]
        self.extract_pdf_to_csv(file_path)

        with open("taxons.csv", "r", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)

            created_count = 0
            updated_count = 0

            for row in reader:
                # TODO Clean up fields assignements + parenthesis
                # Extract sub-embranchement and sous-ordre if present
                embranchement = row["Embranchement (Sous-embranchement)"]
                if "(" in embranchement:
                    embranchement = embranchement.split("(")[0].strip()

                ordre = row["Ordre (Sous-ordre)"]
                if "(" in ordre:
                    ordre = ordre.split("(")[0].strip()

                # Create or update taxon
                taxon, created = Taxon.objects.update_or_create(
                    genre=row["Genre"],
                    espece=row["Espèce"],
                    defaults={
                        "regne": row["Règne"],
                        "embranchement": embranchement,
                        "classe": row["Classe"],
                        "ordre": ordre,
                        "famille": row["Famille"],
                        "nom_vernaculaire": row["Nom vernaculaire"],
                        "partie_etat_indice": row["Partie/état/indice à reconnaitre"],
                    },
                )

                if created:
                    created_count += 1
                    self.stdout.write(f"Created: {taxon.nom_vernaculaire}")
                else:
                    updated_count += 1
                    self.stdout.write(f"Updated: {taxon.nom_vernaculaire}")

        self.stdout.write(self.style.SUCCESS(f"\nImport complete! Created: {created_count}, Updated: {updated_count}"))
