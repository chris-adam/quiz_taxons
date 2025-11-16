from django.db import models


class Taxon(models.Model):
    regne = models.CharField(max_length=100)
    embranchement = models.CharField(max_length=100)
    classe = models.CharField(max_length=100)
    ordre = models.CharField(max_length=100)
    famille = models.CharField(max_length=100)
    genre = models.CharField(max_length=100)
    espece = models.CharField(max_length=100)
    nom_vernaculaire = models.CharField(max_length=200)
    partie_etat_indice = models.CharField(max_length=200)

    last_update = models.DateTimeField(
        blank=True, null=True, help_text="Date de la dernière mise à jour des résultats de recherche d'images"
    )

    def __str__(self):
        return self.nom_vernaculaire


class SearchResult(models.Model):
    taxon = models.ForeignKey(Taxon, on_delete=models.CASCADE, related_name="search_results")
    title = models.CharField(max_length=300)
    link = models.URLField(max_length=500)
    file_format = models.CharField(max_length=100)
    image_context_link = models.URLField(max_length=500)
    image_height = models.IntegerField()
    image_width = models.IntegerField()
    image_byte_size = models.IntegerField()

    def __str__(self):
        return f"{self.taxon.nom_vernaculaire} - {self.title}"


class UserScore(models.Model):
    session_id = models.CharField(max_length=100, db_index=True)
    taxon = models.ForeignKey(Taxon, on_delete=models.CASCADE, related_name="user_scores")
    score = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("session_id", "taxon")
        indexes = [
            models.Index(fields=["session_id", "score"]),
        ]

    def __str__(self):
        return f"{self.session_id[:8]} - {self.taxon.nom_vernaculaire}: {self.score}"
