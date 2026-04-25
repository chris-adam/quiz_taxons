from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import render
from django.template.loader import render_to_string
from taxons.models import SearchResult
from taxons.models import Taxon
from taxons.models import UserScore
from taxons.utils import requests_session

import random
import secrets


CATEGORIES = [
    "Oiseaux",
    "Plantes",
    "Insectes",
    "Araignées",
    "Annélides, mollusques et arthropodes, hors araignées et insectes",
    "Mammifères",
    "Amphibiens et reptiles",
    "Poissons",
    "Mousses, hépatiques, sphaignes, fougères et prêles",
    "Champignons",
    "Lichens",
]


def get_score_lists(session_id, dataset="", category=""):
    qs = UserScore.objects.filter(session_id=session_id)
    if dataset:
        qs = qs.filter(taxon__dataset=dataset)
    if category:
        qs = qs.filter(taxon__category=category)
    all_scores = qs.select_related("taxon").order_by("-score", "-updated_at")
    top_scores = list(all_scores[:10])
    top_ids = [s.id for s in top_scores]
    bottom_scores = list(
        qs.exclude(id__in=top_ids)
        .select_related("taxon")
        .order_by("score", "-updated_at")[:10]
    )
    return top_scores, bottom_scores


def get_or_create_session_id(request):
    if not request.session.get("user_session_id"):
        request.session["user_session_id"] = secrets.token_urlsafe(32)
    return request.session["user_session_id"]


def get_next_taxon(session_id, dataset="", category=""):
    qs = Taxon.objects.all()
    if dataset:
        qs = qs.filter(dataset=dataset)
    if category:
        qs = qs.filter(category=category)

    user_scores = UserScore.objects.filter(session_id=session_id)
    scored_taxon_ids = {score.taxon_id: score.score for score in user_scores}

    all_taxons = list(qs)
    taxon_scores = []
    for taxon in all_taxons:
        score = scored_taxon_ids.get(taxon.id, 0)
        taxon_scores.append((taxon, score))

    if taxon_scores:
        min_score = min(score for _, score in taxon_scores)
        lowest_scoring_taxons = [taxon for taxon, score in taxon_scores if score == min_score]
        return random.choice(lowest_scoring_taxons)

    return None


def index(request):
    session_id = get_or_create_session_id(request)

    dataset = request.GET.get("dataset", "")
    category = request.GET.get("category", "")

    # No dataset selected: show the dataset selector widget
    if not dataset:
        datasets = list(
            Taxon.objects.values_list("dataset", flat=True).distinct().order_by("dataset")
        )
        return render(request, "taxons/index.html", {"datasets": datasets})

    # Reset session when dataset changes
    if dataset != request.session.get("current_dataset", ""):
        for key in ("current_taxon_id", "search_results_ids", "current_score", "current_song_id"):
            request.session.pop(key, None)

    # Reset session when category changes
    if category != request.session.get("current_category", ""):
        for key in ("current_taxon_id", "search_results_ids", "current_score", "current_song_id"):
            request.session.pop(key, None)

    request.session["current_dataset"] = dataset
    request.session["current_category"] = category

    # Clean up session for fresh question
    request.session.pop("current_taxon_id", None)
    request.session.pop("search_results_ids", None)
    request.session.pop("current_score", None)
    request.session.pop("current_song_id", None)

    taxon = get_next_taxon(session_id, dataset=dataset, category=category)
    if not taxon:
        return render(request, "taxons/index.html", {
            "error": "No taxons available.",
            "dataset": dataset,
        })
    request.session["current_taxon_id"] = taxon.id
    request.session["current_score"] = 10

    # Generate propositions filtered to this dataset (and category)
    base_qs = Taxon.objects.filter(dataset=dataset)
    if category:
        base_qs = base_qs.filter(category=category)

    wrong_choices = []
    if taxon.genre:
        wrong_choices.extend(list(base_qs.filter(genre=taxon.genre).exclude(id=taxon.id)))
    if len(wrong_choices) < 3 and taxon.famille:
        wrong_choices.extend(list(
            base_qs.filter(famille=taxon.famille)
            .exclude(id=taxon.id)
            .exclude(id__in=[t.id for t in wrong_choices])
        ))
    if len(wrong_choices) < 3 and taxon.ordre:
        wrong_choices.extend(list(
            base_qs.filter(ordre=taxon.ordre)
            .exclude(id=taxon.id)
            .exclude(id__in=[t.id for t in wrong_choices])
        ))
    if len(wrong_choices) < 3 and taxon.classe:
        wrong_choices.extend(list(
            base_qs.filter(classe=taxon.classe)
            .exclude(id=taxon.id)
            .exclude(id__in=[t.id for t in wrong_choices])
        ))
    if len(wrong_choices) < 3 and taxon.embranchement:
        wrong_choices.extend(list(
            base_qs.filter(embranchement=taxon.embranchement)
            .exclude(id=taxon.id)
            .exclude(id__in=[t.id for t in wrong_choices])
        ))
    if len(wrong_choices) < 3:
        wrong_choices.extend(list(
            base_qs.exclude(id=taxon.id)
            .exclude(id__in=[t.id for t in wrong_choices])
            .order_by("?")
        ))

    selected_wrong = random.sample(wrong_choices, min(3, len(wrong_choices)))
    propositions = [taxon.nom_vernaculaire] + [t.nom_vernaculaire for t in selected_wrong]
    random.shuffle(propositions)

    # Answer dropdown: all nom_vernaculaire in this dataset/category, alphabetical
    nv_qs = Taxon.objects.filter(dataset=dataset)
    if category:
        nv_qs = nv_qs.filter(category=category)
    nom_vernaculaire_list = list(nv_qs.order_by("nom_vernaculaire").values_list("nom_vernaculaire", flat=True))

    top_scores, bottom_scores = get_score_lists(session_id, dataset=dataset, category=category)

    existing_categories = set(
        Taxon.objects.filter(dataset=dataset)
        .exclude(category="")
        .values_list("category", flat=True)
        .distinct()
    )
    categories = [c for c in CATEGORIES if c in existing_categories]

    return render(
        request,
        "taxons/index.html",
        {
            "taxon": taxon,
            "propositions": propositions,
            "top_scores": top_scores,
            "bottom_scores": bottom_scores,
            "dataset": dataset,
            "category": category,
            "categories": categories,
            "nom_vernaculaire_list": nom_vernaculaire_list,
        },
    )


def fetch_images_for_taxon(taxon):
    if taxon.inaturalist_taxon_id is not None:
        taxon_id = taxon.inaturalist_taxon_id
    else:
        if taxon.espece and "spp." not in taxon.espece and "ssp." not in taxon.espece:
            scientific_name = f"{taxon.genre} {taxon.espece}"
        elif taxon.genre:
            scientific_name = taxon.genre
        elif taxon.famille:
            scientific_name = taxon.famille
        elif taxon.ordre:
            scientific_name = taxon.ordre
        elif taxon.classe:
            scientific_name = taxon.classe
        elif taxon.embranchement:
            scientific_name = taxon.embranchement
        elif taxon.regne:
            scientific_name = taxon.regne
        else:
            return

        try:
            taxa_resp = requests_session().get(
                "https://api.inaturalist.org/v1/taxa/autocomplete",
                params={"q": scientific_name, "per_page": 1},
                timeout=10,
            ).json()
            taxa_results = taxa_resp.get("results", [])
            if not taxa_results:
                return
            taxon_id = taxa_results[0]["id"]
        except Exception as e:
            print(f"Error looking up iNaturalist taxon for {scientific_name}: {e}", flush=True)
            return

    try:
        obs_resp = requests_session().get(
            "https://api.inaturalist.org/v1/observations",
            params={
                "taxon_id": taxon_id,
                "place_id": 7008,
                "quality_grade": "research",
                "photos": "true",
                "per_page": 30,
            },
            timeout=15,
        ).json()
        for obs in obs_resp.get("results", []):
            photos = obs.get("photos", [])
            if not photos:
                continue
            photo = photos[0]
            square_url = photo.get("url", "")
            if not square_url:
                continue
            medium_url = square_url.replace("/square.", "/medium.")
            taxon.search_results.create(
                title=photo.get("attribution", "")[:300],
                link=medium_url,
                image_context_link=obs.get("uri", ""),
            )
    except Exception as e:
        print(f"Error fetching iNaturalist observations for {taxon.nom_vernaculaire}: {e}", flush=True)


def fetch_sounds_for_taxon(taxon):
    if taxon.espece and "spp." not in taxon.espece and "ssp." not in taxon.espece:
        species_query = f"gen:{taxon.genre} sp:{taxon.espece}"
    elif taxon.genre:
        species_query = f"gen:{taxon.genre}"
    else:
        return

    queries = [
        f"{species_query} cnt:Belgium type:song",
        f"{species_query} cnt:Belgium",
        f"{species_query} cnt:France type:song",
        f"{species_query} cnt:France",
    ]

    try:
        resp = None
        for query in queries:
            resp = requests_session().get(
                "https://xeno-canto.org/api/3/recordings",
                params={"query": query, "key": settings.XENOCANTO_API_KEY},
                timeout=15,
            ).json()
            if resp.get("recordings"):
                break
        for recording in resp.get("recordings", [])[:30]:
            file_url = recording.get("file", "")
            if not file_url:
                continue
            loc = recording.get("loc", "")
            rec = recording.get("rec", "")
            length = recording.get("length", "")
            attribution = f"{rec} — {loc} ({length})"
            taxon.search_results.create(
                title=attribution[:300],
                link=file_url,
                image_context_link=recording.get("url", ""),
            )
    except Exception as e:
        print(f"Error fetching Xeno-canto sounds for {taxon.nom_vernaculaire}: {e}", flush=True)


def render_images_grid(request, taxon_id):
    taxon = Taxon.objects.get(id=taxon_id)
    is_bird = taxon.classe == "Aves"

    if not taxon.search_results.exists():
        if is_bird:
            fetch_sounds_for_taxon(taxon)
        fetch_images_for_taxon(taxon)

    if not taxon.search_results.exists():
        return HttpResponse(f"Aucun résultat trouvé pour ce taxon (id={taxon.id}).", status=404)

    photos = taxon.search_results.exclude(image_context_link__contains="xeno-canto")

    if request.method == "POST":
        if "current_score" in request.session:
            request.session["current_score"] -= 2

        search_results_ids = request.session.setdefault("search_results_ids", [])
        current_count = len(search_results_ids)
        if current_count == 1:
            more_images = photos.exclude(id__in=search_results_ids).order_by("?")[:1]
        elif current_count == 2:
            more_images = photos.exclude(id__in=search_results_ids).order_by("?")[:2]
        else:
            more_images = []
        request.session["search_results_ids"].extend([img.id for img in more_images])
        request.session.modified = True
    else:
        first_photo = photos.order_by("?").first()
        request.session["search_results_ids"] = [first_photo.id] if first_photo else []
        if is_bird:
            song = taxon.search_results.filter(image_context_link__contains="xeno-canto").order_by("?").first()
            if song:
                request.session["current_song_id"] = song.id

    song = None
    if is_bird:
        song = SearchResult.objects.filter(id=request.session.get("current_song_id")).first()

    images = SearchResult.objects.filter(id__in=request.session["search_results_ids"], taxon=taxon)
    return render(request, "taxons/images_grid.html", {"images": images, "song": song, "taxon": taxon})


def render_result(request):
    session_id = get_or_create_session_id(request)
    category = request.session.get("current_category", "")
    dataset = request.session.get("current_dataset", "")

    taxon_id = request.session.get("current_taxon_id")
    if taxon_id:
        taxon = Taxon.objects.get(id=taxon_id)
        user_answer = request.POST.get("answer", "").strip().lower()
        correct_answer = taxon.nom_vernaculaire.strip().lower()

        if not user_answer:
            result = {}
        elif user_answer == correct_answer:
            current_score = request.session.get("current_score", 10)
            user_score, created = UserScore.objects.get_or_create(
                session_id=session_id, taxon=taxon, defaults={"score": current_score}
            )
            if not created:
                user_score.score += current_score
                user_score.save()
            result = {
                "class": "correct",
                "message": f"✅ Correct ! C'est bien {taxon.nom_vernaculaire}" + (f" ({taxon.genre} {taxon.espece})" if taxon.espece else ""),
            }
        else:
            guessed_taxon = Taxon.objects.filter(nom_vernaculaire=request.POST.get("answer", "").strip()).first()
            if guessed_taxon:
                user_score, created = UserScore.objects.get_or_create(
                    session_id=session_id, taxon=guessed_taxon, defaults={"score": 0}
                )
                if not created:
                    user_score.score = max(0, user_score.score - 5)
                    user_score.save()
            UserScore.objects.get_or_create(session_id=session_id, taxon=taxon, defaults={"score": 0})
            result = {
                "class": "incorrect",
                "message": f"❌ Incorrect. La réponse était : {taxon.nom_vernaculaire}" + (f" ({taxon.genre} {taxon.espece})" if taxon.espece else ""),
            }
    else:
        result = {
            "class": "incorrect",
            "message": "❌ No active question",
        }

    top_scores, bottom_scores = get_score_lists(session_id, dataset=dataset, category=category)
    result_html = render_to_string("taxons/result.html", {"result": result, "category": category, "dataset": dataset}, request=request)
    portlet_html = render_to_string(
        "taxons/scores_portlet.html",
        {"top_scores": top_scores, "bottom_scores": bottom_scores, "oob": True},
        request=request,
    )
    return HttpResponse(result_html + portlet_html)


def show_propositions(request):
    request.session["current_score"] -= 5
    request.session.modified = True
    return HttpResponse(status=204)


def skip_question(request):
    request.session.pop("current_taxon_id", None)
    request.session.pop("search_results_ids", None)
    request.session.pop("current_score", None)
    return HttpResponse(status=200, headers={"HX-Refresh": "true"})
