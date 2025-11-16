import random
import secrets
import urllib.parse

import requests
from django.http import HttpResponse
from django.shortcuts import render

from quiz.settings import GOOGLE_SEARCH_API_KEY
from quiz.settings import GOOGLE_SEARCH_ENGINE
from taxons.models import SearchResult
from taxons.models import Taxon
from taxons.models import UserScore


def get_or_create_session_id(request):
    """Get or create a session ID for the user"""
    if not request.session.get("user_session_id"):
        request.session["user_session_id"] = secrets.token_urlsafe(32)
    return request.session["user_session_id"]


def get_next_taxon(session_id):
    """
    Select next taxon based on lowest score.
    Prioritize taxons the user has never seen (score 0) or struggled with.
    """
    # Get all user scores for this session
    user_scores = UserScore.objects.filter(session_id=session_id)

    # Get all taxon IDs and their scores
    scored_taxon_ids = {score.taxon_id: score.score for score in user_scores}

    # Get all taxons
    all_taxons = list(Taxon.objects.all())

    # Create a list of (taxon, score) tuples
    taxon_scores = []
    for taxon in all_taxons:
        score = scored_taxon_ids.get(taxon.id, 0)  # Default score is 0 for unseen taxons
        taxon_scores.append((taxon, score))

    # Find the minimum score
    if taxon_scores:
        min_score = min(score for _, score in taxon_scores)
        # Get all taxons with the minimum score
        lowest_scoring_taxons = [taxon for taxon, score in taxon_scores if score == min_score]
        # Randomly select one
        return random.choice(lowest_scoring_taxons)

    return None


def index(request):
    # Ensure user has a session ID
    session_id = get_or_create_session_id(request)

    # Clean up session
    request.session.pop("current_taxon_id", None)
    request.session.pop("search_results_ids", None)
    request.session.pop("current_score", None)

    # Get or create current taxon
    taxon_id = request.session.get("current_taxon_id")
    if not taxon_id:
        taxon = get_next_taxon(session_id)
        if not taxon:
            return render(request, "taxons/index.html", {"error": "No taxons available."})
        request.session["current_taxon_id"] = taxon.id
        request.session["current_score"] = 10  # Start with max score
    else:
        taxon = Taxon.objects.get(id=taxon_id)

    # Generate 4 propositions (including the correct answer)
    # Prioritize taxons from the same taxonomic levels for harder quiz
    wrong_choices = []

    # Try to get taxons from same genus (if available)
    if taxon.genre:
        same_genus = list(Taxon.objects.filter(genre=taxon.genre).exclude(id=taxon.id))
        wrong_choices.extend(same_genus)

    # If not enough, get from same family
    if len(wrong_choices) < 3 and taxon.famille:
        same_family = list(
            Taxon.objects.filter(famille=taxon.famille)
            .exclude(id=taxon.id)
            .exclude(id__in=[t.id for t in wrong_choices])
        )
        wrong_choices.extend(same_family)

    # If still not enough, get from same order
    if len(wrong_choices) < 3 and taxon.ordre:
        same_order = list(
            Taxon.objects.filter(ordre=taxon.ordre).exclude(id=taxon.id).exclude(id__in=[t.id for t in wrong_choices])
        )
        wrong_choices.extend(same_order)

    # If still not enough, get from same class
    if len(wrong_choices) < 3 and taxon.classe:
        same_class = list(
            Taxon.objects.filter(classe=taxon.classe).exclude(id=taxon.id).exclude(id__in=[t.id for t in wrong_choices])
        )
        wrong_choices.extend(same_class)

    # If still not enough, get from same embranchement
    if len(wrong_choices) < 3 and taxon.embranchement:
        same_embranchement = list(
            Taxon.objects.filter(embranchement=taxon.embranchement)
            .exclude(id=taxon.id)
            .exclude(id__in=[t.id for t in wrong_choices])
        )
        wrong_choices.extend(same_embranchement)

    # If still not enough, get random taxons
    if len(wrong_choices) < 3:
        random_taxons = list(
            Taxon.objects.exclude(id=taxon.id).exclude(id__in=[t.id for t in wrong_choices]).order_by("?")
        )
        wrong_choices.extend(random_taxons)

    # Select 3 wrong choices randomly from the pool
    selected_wrong = random.sample(wrong_choices, min(3, len(wrong_choices)))
    propositions = [taxon.nom_vernaculaire] + [t.nom_vernaculaire for t in selected_wrong]
    random.shuffle(propositions)

    return render(
        request,
        "taxons/index.html",
        {
            "taxon": taxon,
            "propositions": propositions,
        },
    )


def fetch_images_for_taxon(taxon):
    """Fetch images from Google Custom Search API"""

    # Determine the lowest available taxonomy level
    if taxon.espece:
        # Use binomial name (genus + species)
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
        scientific_name = ""

    for partie_etat_indice in taxon.partie_etat_indice.split(" + "):
        query = {
            "key": GOOGLE_SEARCH_API_KEY,
            "cx": GOOGLE_SEARCH_ENGINE,
            "num": 10,
            "searchType": "image",
            "q": f"{taxon.nom_vernaculaire} {scientific_name} {partie_etat_indice}",
        }
        url = "https://www.googleapis.com/customsearch/v1?" + urllib.parse.urlencode(query)

        try:
            json_results = requests.get(url).json()
            for item in json_results.get("items", []):
                taxon.search_results.create(
                    title=item.get("title", "")[:300],
                    link=item.get("link", ""),
                    file_format=item.get("fileFormat", ""),
                    image_context_link=item.get("image", {}).get("contextLink", ""),
                    image_height=item.get("image", {}).get("height", 0),
                    image_width=item.get("image", {}).get("width", 0),
                    image_byte_size=item.get("image", {}).get("byteSize", 0),
                )
        except Exception as e:
            print(f"Error fetching images for {taxon.nom_vernaculaire}: {e}")


def render_images_grid(request, taxon_id):
    """Render image grid for a given taxon (for HTMX requests)"""

    taxon = Taxon.objects.get(id=taxon_id)

    # Fetch or create search results
    search_results = taxon.search_results.all()
    if not search_results:
        fetch_images_for_taxon(taxon)
        search_results = taxon.search_results.all()

    if not search_results:
        return render(request, "taxons/index.html", {"error": "No images found for this taxon."})

    if request.method == "POST":
        # Deduct 2 points for requesting more images
        if "current_score" in request.session:
            request.session["current_score"] -= 2

        search_results_ids = request.session.setdefault("search_results_ids", [])
        current_count = len(search_results_ids)
        if current_count == 1:
            more_images = taxon.search_results.exclude(id__in=search_results_ids).order_by("?")[:1]
        elif current_count == 2:
            more_images = taxon.search_results.exclude(id__in=search_results_ids).order_by("?")[:2]
        else:
            more_images = []
        request.session["search_results_ids"].extend([img.id for img in more_images])
        request.session.modified = True
    else:
        request.session["search_results_ids"] = [search_results.order_by("?").first().id]

    try:
        images = SearchResult.objects.filter(id__in=request.session["search_results_ids"], taxon=taxon)
        return render(request, "taxons/images_grid.html", {"images": images, "taxon": taxon})
    except Taxon.DoesNotExist:
        return HttpResponse("Taxon not found.", status=404)


def render_result(request):
    """Render result snippet for HTMX requests"""
    session_id = get_or_create_session_id(request)

    # Check answer
    taxon_id = request.session.get("current_taxon_id")
    if taxon_id:
        taxon = Taxon.objects.get(id=taxon_id)
        user_answer = request.POST.get("answer", "").strip().lower()
        correct_answer = taxon.nom_vernaculaire.strip().lower()

        if not user_answer:
            result = {}
        elif user_answer == correct_answer:
            # Get current score and save it
            current_score = request.session.get("current_score", 10)

            # Update or create user score
            user_score, created = UserScore.objects.get_or_create(
                session_id=session_id, taxon=taxon, defaults={"score": current_score}
            )
            if not created:
                # Add to existing score
                user_score.score += current_score
                user_score.save()

            result = {
                "class": "correct",
                "message": f"✅ Correct ! C'est bien {taxon.nom_vernaculaire} ({taxon.genre} {taxon.espece})",
            }
        else:
            # Wrong answer - deduct 5 points from the guessed taxon
            try:
                guessed_taxon = Taxon.objects.get(nom_vernaculaire=request.POST.get("answer", "").strip())
                user_score, created = UserScore.objects.get_or_create(
                    session_id=session_id, taxon=guessed_taxon, defaults={"score": -1}
                )
                if not created:
                    user_score.score = max(-1, user_score.score - 5)
                    user_score.save()
            except Taxon.DoesNotExist:
                # User entered a taxon that doesn't exist in database, ignore
                pass

            result = {
                "class": "incorrect",
                "message": f"❌ Incorrect. La réponse était : {taxon.nom_vernaculaire} ({taxon.genre} {taxon.espece})",
            }
    else:
        result = {
            "class": "incorrect",
            "message": "❌ No active question",
        }

    return render(request, "taxons/result.html", {"result": result})


def show_propositions(request):
    """Deduct points when user requests propositions (HTMX endpoint)"""
    request.session["current_score"] -= 5
    request.session.modified = True
    return HttpResponse(status=204)  # No content response


def skip_question(request):
    """Skip current question and reset session"""
    request.session.pop("current_taxon_id", None)
    request.session.pop("search_results_ids", None)
    request.session.pop("current_score", None)
    return HttpResponse(status=200, headers={"HX-Refresh": "true"})


def get_taxonomy_options(request):
    """Get options for all taxonomy levels based on current selections"""
    level = request.GET.get("level", "")
    regne = request.GET.get("regne", "")
    embranchement = request.GET.get("embranchement", "")
    classe = request.GET.get("classe", "")
    ordre = request.GET.get("ordre", "")
    famille = request.GET.get("famille", "")
    genre = request.GET.get("genre", "")
    espece = request.GET.get("espece", "")
    nom_vernaculaire = request.GET.get("nom_vernaculaire", "")

    # When a level changes, reset all levels below it and fill upper levels if needed
    if level == "regne":
        embranchement = classe = ordre = famille = genre = espece = nom_vernaculaire = ""
    elif level == "embranchement":
        classe = ordre = famille = genre = espece = nom_vernaculaire = ""
    elif level == "classe":
        ordre = famille = genre = espece = nom_vernaculaire = ""
    elif level == "ordre":
        famille = genre = espece = nom_vernaculaire = ""
    elif level == "famille":
        genre = espece = nom_vernaculaire = ""
    elif level == "genre":
        espece = nom_vernaculaire = ""
    elif level == "espece":
        nom_vernaculaire = ""
    elif level == "nom_vernaculaire":
        # Fill in all upper levels from the selected nom_vernaculaire
        if nom_vernaculaire:
            taxon = Taxon.objects.filter(nom_vernaculaire=nom_vernaculaire).first()
            if taxon:
                regne = taxon.regne
                embranchement = taxon.embranchement
                classe = taxon.classe
                ordre = taxon.ordre
                famille = taxon.famille
                genre = taxon.genre
                espece = taxon.espece

    # If a lower level is selected, auto-fill upper levels
    if espece and not genre:
        taxon = Taxon.objects.filter(espece=espece).first()
        if taxon:
            regne = taxon.regne
            embranchement = taxon.embranchement
            classe = taxon.classe
            ordre = taxon.ordre
            famille = taxon.famille
            genre = taxon.genre

    if genre and not famille:
        taxon = Taxon.objects.filter(genre=genre).first()
        if taxon:
            regne = taxon.regne
            embranchement = taxon.embranchement
            classe = taxon.classe
            ordre = taxon.ordre
            famille = taxon.famille

    if famille and not ordre:
        taxon = Taxon.objects.filter(famille=famille).first()
        if taxon:
            regne = taxon.regne
            embranchement = taxon.embranchement
            classe = taxon.classe
            ordre = taxon.ordre

    if ordre and not classe:
        taxon = Taxon.objects.filter(ordre=ordre).first()
        if taxon:
            regne = taxon.regne
            embranchement = taxon.embranchement
            classe = taxon.classe

    if classe and not embranchement:
        taxon = Taxon.objects.filter(classe=classe).first()
        if taxon:
            regne = taxon.regne
            embranchement = taxon.embranchement

    if embranchement and not regne:
        taxon = Taxon.objects.filter(embranchement=embranchement).first()
        if taxon:
            regne = taxon.regne

    # Build base query
    query = Taxon.objects.all()
    if regne:
        query = query.filter(regne=regne)
    if embranchement:
        query = query.filter(embranchement=embranchement)
    if classe:
        query = query.filter(classe=classe)
    if ordre:
        query = query.filter(ordre=ordre)
    if famille:
        query = query.filter(famille=famille)
    if genre:
        query = query.filter(genre=genre)
    if espece:
        query = query.filter(espece=espece)

    # Get options for each level
    context = {
        "regne": regne,
        "embranchement": embranchement,
        "classe": classe,
        "ordre": ordre,
        "famille": famille,
        "genre": genre,
        "espece": espece,
        "nom_vernaculaire": nom_vernaculaire,
    }

    # Always show all regnes
    context["regne_options"] = list(
        Taxon.objects.values_list("regne", flat=True).distinct().exclude(regne="").order_by("regne")
    )

    # Show embranchements for selected regne (or all if none selected)
    emb_query = Taxon.objects.all()
    if regne:
        emb_query = emb_query.filter(regne=regne)
    context["embranchement_options"] = list(
        emb_query.values_list("embranchement", flat=True).distinct().exclude(embranchement="").order_by("embranchement")
    )

    # Show classes for selected regne/embranchement
    classe_query = Taxon.objects.all()
    if regne:
        classe_query = classe_query.filter(regne=regne)
    if embranchement:
        classe_query = classe_query.filter(embranchement=embranchement)
    context["classe_options"] = list(
        classe_query.values_list("classe", flat=True).distinct().exclude(classe="").order_by("classe")
    )

    # Show ordres for selected upper levels
    ordre_query = Taxon.objects.all()
    if regne:
        ordre_query = ordre_query.filter(regne=regne)
    if embranchement:
        ordre_query = ordre_query.filter(embranchement=embranchement)
    if classe:
        ordre_query = ordre_query.filter(classe=classe)
    context["ordre_options"] = list(
        ordre_query.values_list("ordre", flat=True).distinct().exclude(ordre="").order_by("ordre")
    )

    # Show familles
    famille_query = Taxon.objects.all()
    if regne:
        famille_query = famille_query.filter(regne=regne)
    if embranchement:
        famille_query = famille_query.filter(embranchement=embranchement)
    if classe:
        famille_query = famille_query.filter(classe=classe)
    if ordre:
        famille_query = famille_query.filter(ordre=ordre)
    context["famille_options"] = list(
        famille_query.values_list("famille", flat=True).distinct().exclude(famille="").order_by("famille")
    )

    # Show genres
    genre_query = Taxon.objects.all()
    if regne:
        genre_query = genre_query.filter(regne=regne)
    if embranchement:
        genre_query = genre_query.filter(embranchement=embranchement)
    if classe:
        genre_query = genre_query.filter(classe=classe)
    if ordre:
        genre_query = genre_query.filter(ordre=ordre)
    if famille:
        genre_query = genre_query.filter(famille=famille)
    context["genre_options"] = list(
        genre_query.values_list("genre", flat=True).distinct().exclude(genre="").order_by("genre")
    )

    # Show especes
    espece_query = Taxon.objects.all()
    if regne:
        espece_query = espece_query.filter(regne=regne)
    if embranchement:
        espece_query = espece_query.filter(embranchement=embranchement)
    if classe:
        espece_query = espece_query.filter(classe=classe)
    if ordre:
        espece_query = espece_query.filter(ordre=ordre)
    if famille:
        espece_query = espece_query.filter(famille=famille)
    if genre:
        espece_query = espece_query.filter(genre=genre)
    context["espece_options"] = list(
        espece_query.values_list("espece", flat=True).distinct().exclude(espece="").order_by("espece")
    )

    # Show nom_vernaculaire (final selection)
    context["nom_vernaculaire_options"] = list(
        query.values_list("nom_vernaculaire", flat=True).distinct().order_by("nom_vernaculaire")
    )

    return render(request, "taxons/taxonomy_select.html", context)
