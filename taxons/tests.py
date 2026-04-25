from django.test import TestCase, Client, override_settings
from taxons.models import Taxon, UserScore
from taxons.views import get_next_taxon, get_score_lists


def make_taxon(dataset="nature", nom_vernaculaire="Merle noir", category="Oiseaux",
               genre="Turdus", espece="merula", classe="Aves", ordre="Passeriformes",
               famille="Turdidae", **kwargs):
    return Taxon.objects.create(
        dataset=dataset,
        nom_vernaculaire=nom_vernaculaire,
        category=category,
        genre=genre,
        espece=espece,
        classe=classe,
        ordre=ordre,
        famille=famille,
        regne="Animalia",
        embranchement="Chordata",
        partie_etat_indice="",
        **kwargs,
    )


class TaxonDatasetFieldTest(TestCase):
    def test_default_dataset_is_empty_string(self):
        t = Taxon.objects.create(
            nom_vernaculaire="Test",
            genre="Genus", espece="species",
            regne="R", embranchement="E", classe="C",
            ordre="O", famille="F", partie_etat_indice="",
        )
        self.assertEqual(t.dataset, "")

    def test_dataset_stores_nature(self):
        t = make_taxon(dataset="nature")
        t.refresh_from_db()
        self.assertEqual(t.dataset, "nature")

    def test_dataset_stores_rando(self):
        t = make_taxon(dataset="rando", nom_vernaculaire="Chêne rouge",
                       genre="Quercus", espece="rubra", category="Plantes",
                       classe="Magnoliopsida")
        t.refresh_from_db()
        self.assertEqual(t.dataset, "rando")

    def test_same_genre_espece_different_datasets_are_separate_records(self):
        make_taxon(dataset="nature")
        make_taxon(dataset="rando")
        self.assertEqual(Taxon.objects.filter(genre="Turdus", espece="merula").count(), 2)


class GetScoreListsTest(TestCase):
    def setUp(self):
        self.session_id = "testsession"
        self.t_nature = make_taxon(dataset="nature", nom_vernaculaire="Merle noir",
                                   genre="Turdus", espece="merula", category="Oiseaux")
        self.t_rando = make_taxon(dataset="rando", nom_vernaculaire="Chêne rouge",
                                  genre="Quercus", espece="rubra", category="Plantes",
                                  classe="Magnoliopsida")
        UserScore.objects.create(session_id=self.session_id, taxon=self.t_nature, score=10)
        UserScore.objects.create(session_id=self.session_id, taxon=self.t_rando, score=5)

    def test_no_filter_returns_all(self):
        top, bottom = get_score_lists(self.session_id)
        all_taxons = [s.taxon for s in top + bottom]
        self.assertIn(self.t_nature, all_taxons)
        self.assertIn(self.t_rando, all_taxons)

    def test_dataset_filter_returns_only_that_dataset(self):
        top, bottom = get_score_lists(self.session_id, dataset="nature")
        all_taxons = [s.taxon for s in top + bottom]
        self.assertIn(self.t_nature, all_taxons)
        self.assertNotIn(self.t_rando, all_taxons)

    def test_dataset_and_category_intersection(self):
        top, bottom = get_score_lists(self.session_id, dataset="nature", category="Plantes")
        self.assertEqual(top + bottom, [])


class GetNextTaxonTest(TestCase):
    def setUp(self):
        self.session_id = "testsession"
        self.t_nature = make_taxon(dataset="nature", nom_vernaculaire="Merle noir",
                                   genre="Turdus", espece="merula", category="Oiseaux")
        self.t_rando = make_taxon(dataset="rando", nom_vernaculaire="Chêne rouge",
                                  genre="Quercus", espece="rubra", category="Plantes",
                                  classe="Magnoliopsida")

    def test_no_filter_returns_a_taxon(self):
        result = get_next_taxon(self.session_id)
        self.assertIsNotNone(result)

    def test_dataset_filter_returns_only_that_dataset(self):
        for _ in range(10):
            result = get_next_taxon(self.session_id, dataset="nature")
            self.assertEqual(result.dataset, "nature")

    def test_dataset_rando_filter(self):
        for _ in range(10):
            result = get_next_taxon(self.session_id, dataset="rando")
            self.assertEqual(result.dataset, "rando")

    def test_no_match_returns_none(self):
        result = get_next_taxon(self.session_id, dataset="nonexistent")
        self.assertIsNone(result)


@override_settings(STORAGES={
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
})
class IndexViewDatasetTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.t1 = make_taxon(dataset="nature", nom_vernaculaire="Merle noir",
                              genre="Turdus", espece="merula")
        self.t2 = make_taxon(dataset="rando", nom_vernaculaire="Chêne rouge",
                              genre="Quercus", espece="rubra", category="Plantes",
                              classe="Magnoliopsida")

    def test_no_dataset_renders_selector(self):
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("datasets", resp.context)
        self.assertNotIn("taxon", resp.context)

    def test_datasets_list_contains_available_datasets(self):
        resp = self.client.get("/")
        self.assertIn("nature", resp.context["datasets"])
        self.assertIn("rando", resp.context["datasets"])

    def test_with_dataset_renders_quiz(self):
        resp = self.client.get("/?dataset=nature")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("taxon", resp.context)
        self.assertEqual(resp.context["taxon"].dataset, "nature")

    def test_session_stores_current_dataset(self):
        self.client.get("/?dataset=nature")
        session = self.client.session
        self.assertEqual(session["current_dataset"], "nature")
