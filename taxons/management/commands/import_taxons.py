from datetime import datetime
from django.conf import settings
from django.core.management.base import BaseCommand
from django.core.management.base import CommandError
from taxons.models import Taxon

import csv
import os
import pdfplumber
import requests
import time


CATEGORY_MAP = {
    # Oiseaux
    "Accenteur mouchet": "Oiseaux",
    "Alouette des champs": "Oiseaux",
    "Bergeronnette grise": "Oiseaux",
    "Bergeronnette printanière": "Oiseaux",
    "Bernache du Canada": "Oiseaux",
    "Bouvreuil pivoine": "Oiseaux",
    "Bruant jaune": "Oiseaux",
    "Buse variable": "Oiseaux",
    "Canard colvert": "Oiseaux",
    "Chardonneret élégant": "Oiseaux",
    "Chevêche d’Athéna": "Oiseaux",
    "Choucas des tours": "Oiseaux",
    "Chouette hulotte": "Oiseaux",
    "Cigogne blanche": "Oiseaux",
    "Corbeau freux": "Oiseaux",
    "Corneille noire": "Oiseaux",
    "Cygne tuberculé": "Oiseaux",
    "Effraie des clochers": "Oiseaux",
    "Épervier d’Europe": "Oiseaux",
    "Étourneau sanson net": "Oiseaux",
    "Faucon crécerelle": "Oiseaux",
    "Fauvette à tête noire": "Oiseaux",
    "Foulque macroule": "Oiseaux",
    "Fuligule morillon": "Oiseaux",
    "Gallinule poule-d’eau": "Oiseaux",
    "Geai des chênes": "Oiseaux",
    "Goélands": "Oiseaux",
    "Grand cormoran": "Oiseaux",
    "Grèbe huppé": "Oiseaux",
    "Grimpereaux": "Oiseaux",
    "Grive draine": "Oiseaux",
    "Grive litorne": "Oiseaux",
    "Grive musicienne": "Oiseaux",
    "Grosbec casse-noyaux": "Oiseaux",
    "Héron cendré": "Oiseaux",
    "Hirondelle de fenêtre": "Oiseaux",
    "Hirondelle rustique": "Oiseaux",
    "Huîtrier pie": "Oiseaux",
    "Linotte mélodieuse": "Oiseaux",
    "Martin-pêcheur d’Europe": "Oiseaux",
    "Martinet noir": "Oiseaux",
    "Merle noir": "Oiseaux",
    "Mésange bleue": "Oiseaux",
    "Mésange charbon nière": "Oiseaux",
    "Milan royal": "Oiseaux",
    "Moineau domes tique": "Oiseaux",
    "Mouette rieuse": "Oiseaux",
    "Orite à longue queue": "Oiseaux",
    "Ouette d’Égypte": "Oiseaux",
    "Perruche à collier": "Oiseaux",
    "Pic épeiche": "Oiseaux",
    "Pic vert": "Oiseaux",
    "Pie bavarde": "Oiseaux",
    "Pigeon biset domestique": "Oiseaux",
    "Pigeon ramier": "Oiseaux",
    "Pinson des arbres": "Oiseaux",
    "Pouillot véloce": "Oiseaux",
    "Roitelets": "Oiseaux",
    "Rougegorge familier": "Oiseaux",
    "Rougequeue noir": "Oiseaux",
    "Sittelle torchepot": "Oiseaux",
    "Tarier pâtre": "Oiseaux",
    "Tourterelle turque": "Oiseaux",
    "Troglodyte mignon": "Oiseaux",
    "Vanneau huppé": "Oiseaux",
    "Verdier d’Europe": "Oiseaux",
    "Bergeronnette des ruisseaux": "Oiseaux",
    "Cincle plongeur": "Oiseaux",
    "Grand Cormoran": "Oiseaux",
    "Grande Aigrette": "Oiseaux",
    "Hirondelle des fenêtres": "Oiseaux",
    "Martin-pêcheur d’Europe": "Oiseaux",
    "Mésange charbonnière": "Oiseaux",
    "Pic noir": "Oiseaux",
    "Roitelet huppé": "Oiseaux",
    "Roitelet triple-bandeau": "Oiseaux",

    # Plantes
    "Achillée millefeuille": "Plantes",
    "Aigremoines": "Plantes",
    "Ail des ours": "Plantes",
    "Alchémilles": "Plantes",
    "Alliaire officinale": "Plantes",
    "Ancolie commune": "Plantes",
    "Anémone sylvie": "Plantes",
    "Angélique sauvage": "Plantes",
    "Arbre aux papillons": "Plantes",
    "Armoise commune": "Plantes",
    "Aspérule odorante": "Plantes",
    "Aubépine à deux styles": "Plantes",
    "Aubépine à un style": "Plantes",
    "Aulne glutineux": "Plantes",
    "Balsamine des bois": "Plantes",
    "Balsamine glanduleuse": "Plantes",
    "Bardanes": "Plantes",
    "Benoîte commune": "Plantes",
    "Berce commune": "Plantes",
    "Berce du Caucase": "Plantes",
    "Bleuet des champs": "Plantes",
    "Bouillon blanc": "Plantes",
    "Bouleau pubescent": "Plantes",
    "Bouleau verruqueux": "Plantes",
    "Bourdaine": "Plantes",
    "Bourse-à-pasteur": "Plantes",
    "Brunelle commune": "Plantes",
    "Bugle rampante": "Plantes",
    "Buis": "Plantes",
    "Butome en ombelle": "Plantes",
    "Cabaret des oiseaux": "Plantes",
    "Callune": "Plantes",
    "Campanule à feuilles rondes": "Plantes",
    "Cardamine amère": "Plantes",
    "Cardamine des prés": "Plantes",
    "Carotte sauvage": "Plantes",
    "Cerfeuil sauvage": "Plantes",
    "Cerisier à grappes": "Plantes",
    "Cerisier tardif": "Plantes",
    "Charme": "Plantes",
    "Châtaignier": "Plantes",
    "Chêne pédonculé": "Plantes",
    "Chêne rouge d'Amérique": "Plantes",
    "Chêne sessile": "Plantes",
    "Chèvrefeuille des bois": "Plantes",
    "Chicorée sauvage": "Plantes",
    "Circée de Paris": "Plantes",
    "Cirses": "Plantes",
    "Clématite des haies": "Plantes",
    "Colchique d'automne": "Plantes",
    "Compagnon blanc": "Plantes",
    "Compagnon rouge": "Plantes",
    "Consoude officinale": "Plantes",
    "Coquelicots": "Plantes",
    "Cornouiller sanguin": "Plantes",
    "Digitale pourpre": "Plantes",
    "Douglas": "Plantes",
    "Églantier": "Plantes",
    "Épervière piloselle": "Plantes",
    "Épiaire des bois": "Plantes",
    "Épicéa commun": "Plantes",
    "Épilobe à feuilles étroites": "Plantes",
    "Épilobe hirsute": "Plantes",
    "Érable champêtre": "Plantes",
    "Érable plane": "Plantes",
    "Érable sycomore": "Plantes",
    "Eupatoire chanvrine": "Plantes",
    "Euphorbe des bois": "Plantes",
    "Euphorbe réveil-matin": "Plantes",
    "Ficaire fausse-renoncule": "Plantes",
    "Fleur de coucou": "Plantes",
    "Fraisier des bois": "Plantes",
    "Framboisier": "Plantes",
    "Frêne commun": "Plantes",
    "Fusain d'Europe": "Plantes",
    "Gaillet blanc": "Plantes",
    "Gaillet croisette": "Plantes",
    "Gaillet gratteron": "Plantes",
    "Galéopsis tétrahit": "Plantes",
    "Genêt à balais": "Plantes",
    "Genévrier commun": "Plantes",
    "Germandrée scorodoine": "Plantes",
    "Gesses": "Plantes",
    "Gouet tacheté": "Plantes",
    "Grande chélidoine": "Plantes",
    "Grande marguerite": "Plantes",
    "Groseilliers": "Plantes",
    "Gui": "Plantes",
    "Herbe à Robert": "Plantes",
    "Herbe aux écus": "Plantes",
    "Hêtre": "Plantes",
    "Houblon": "Plantes",
    "Houx": "Plantes",
    "If": "Plantes",
    "Iris jaune": "Plantes",
    "Jacinthe des bois": "Plantes",
    "Jonc épars": "Plantes",
    "Jonquille": "Plantes",
    "Laiteron rude": "Plantes",
    "Lamier blanc": "Plantes",
    "Lamier jaune": "Plantes",
    "Lamier pourpre": "Plantes",
    "Lentilles": "Plantes",
    "Lierre (grimpant)": "Plantes",
    "Lierre terrestre": "Plantes",
    "Linaire commune": "Plantes",
    "Liseron des champs": "Plantes",
    "Liseron des haies": "Plantes",
    "Lotier corniculé": "Plantes",
    "Luzerne cultivée": "Plantes",
    "Marronnier d'Inde": "Plantes",
    "Massettes": "Plantes",
    "Matricaire discoïde": "Plantes",
    "Mélampyre des prés": "Plantes",
    "Mélèzes": "Plantes",
    "Mélilots": "Plantes",
    "Mercuriale annuelle": "Plantes",
    "Merisier": "Plantes",
    "Millepertuis perforé": "Plantes",
    "Minette": "Plantes",
    "Mouron des oiseaux": "Plantes",
    "Mouron rouge": "Plantes",
    "Muguet": "Plantes",
    "Myrtille": "Plantes",
    "Nénufar blanc": "Plantes",
    "Nénufar jaune": "Plantes",
    "Noisetier": "Plantes",
    "Noyers": "Plantes",
    "Onagres": "Plantes",
    "Orme": "Plantes",
    "Orpins": "Plantes",
    "Ortie dioïque": "Plantes",
    "Oseilles": "Plantes",
    "Pâquerette": "Plantes",
    "Parisette": "Plantes",
    "Perce-neige": "Plantes",
    "Petite pervenche": "Plantes",
    "Peuplier tremble": "Plantes",
    "Peupliers": "Plantes",
    "Pin sylvestre": "Plantes",
    "Pissenlits": "Plantes",
    "Plantain à larges feuilles": "Plantes",
    "Plantain lancéolé": "Plantes",
    "Plantains d’eau": "Plantes",
    "Poirier sauvage": "Plantes",
    "Pommier sauvage": "Plantes",
    "Populage des marais": "Plantes",
    "Potentille des oies": "Plantes",
    "Potentille rampante": "Plantes",
    "Primevère élevée": "Plantes",
    "Primevère officinale": "Plantes",
    "Prunellier": "Plantes",
    "Pulmonaire officinale": "Plantes",
    "Reine-des-prés": "Plantes",
    "Renoncule flottante": "Plantes",
    "Renoncule rampante": "Plantes",
    "Renouée amphibie": "Plantes",
    "Renouée du Japon": "Plantes",
    "Renouée persicaire": "Plantes",
    "Robinier faux-acacia": "Plantes",
    "Ronces": "Plantes",
    "Roseau": "Plantes",
    "Rossolis à feuilles rondes": "Plantes",
    "Ruine de Rome": "Plantes",
    "Salicaire commune": "Plantes",
    "Salicornes": "Plantes",
    "Salsifis des prés": "Plantes",
    "Saule blanc": "Plantes",
    "Saule marsault": "Plantes",
    "Sceau-de-Salomon multiflore": "Plantes",
    "Scrofulaire noueuse": "Plantes",
    "Séneçon commun": "Plantes",
    "Séneçon jacobée": "Plantes",
    "Sorbier des oiseleurs": "Plantes",
    "Stellaire holostée": "Plantes",
    "Sureau à grappes": "Plantes",
    "Sureau noir": "Plantes",
    "Surelle": "Plantes",
    "Symphorine blanche": "Plantes",
    "Tabouret des champs": "Plantes",
    "Tanaisie": "Plantes",
    "Tilleul à larges feuilles": "Plantes",
    "Tilleul à petites feuilles": "Plantes",
    "Trèfle des prés": "Plantes",
    "Trèfle rampant": "Plantes",
    "Troène commun": "Plantes",
    "Tussilage": "Plantes",
    "Valériane officinale": "Plantes",
    "Véroniques": "Plantes",
    "Vesces": "Plantes",
    "Violettes": "Plantes",
    "Viorne mancienne": "Plantes",
    "Viorne obier": "Plantes",
    "Vipérine commune": "Plantes",
    "Aubépine sp.": "Plantes",
    "Chêne rouge": "Plantes",
    "Cornouiller sp.": "Plantes",
    "Epicéa": "Plantes",
    "Frêne élevé": "Plantes",
    "Houx commun": "Plantes",
    "Sureau sp.": "Plantes",
    "Genévrier": "Plantes",
    "Mélèze d'Europe": "Plantes",
    "Pin noir": "Plantes",
    "Aconit tue-loup": "Plantes",
    "Alchémille vert jaunâtre": "Plantes",
    "Campanule sp.": "Plantes",
    "Dompte-venin": "Plantes",
    "Epilobe en épi": "Plantes",
    "Grande Consoude": "Plantes",
    "Hellébore fétide": "Plantes",
    "Orchis de Fuchs": "Plantes",
    "Orchis mâle": "Plantes",
    "Plantain majeur": "Plantes",
    "Silène enflé": "Plantes",
    "Silène penché": "Plantes",
    "Silène rouge": "Plantes",

    # Insectes
    "Abeille domestique": "Insectes",
    "Adèles": "Insectes",
    "Aeschnes": "Insectes",
    "Agrions": "Insectes",
    "Anax empereur": "Insectes",
    "Asiles": "Insectes",
    "Azuré commun": "Insectes",
    "Belle-dame": "Insectes",
    "Blattes": "Insectes",
    "Bombyles": "Insectes",
    "Bourdons": "Insectes",
    "Caloptéryx": "Insectes",
    "Cantharides": "Insectes",
    "Carabes": "Insectes",
    "Cercope sanguin": "Insectes",
    "Cétoine dorée": "Insectes",
    "Charançons": "Insectes",
    "Chrysomèles": "Insectes",
    "Chrysopes": "Insectes",
    "Cicindèle champêtre": "Insectes",
    "Cigariers": "Insectes",
    "Coccinelle à sept points": "Insectes",
    "Coccinelle asiatique": "Insectes",
    "Corée marginé": "Insectes",
    "Criquet à ailes bleues": "Insectes",
    "Criquet des pâtures": "Insectes",
    "Cynips de la galle-cerise du chêne": "Insectes",
    "Cynips de la pomme de chêne": "Insectes",
    "Cynips du rosier/Bédégar": "Insectes",
    "Decticelle cendrée": "Insectes",
    "Dytiques": "Insectes",
    "Écaille chinée": "Insectes",
    "Empidides": "Insectes",
    "Fourmis": "Insectes",
    "Frelon européen": "Insectes",
    "Gendarme": "Insectes",
    "Géomètres": "Insectes",
    "Géotrupes": "Insectes",
    "Gerris": "Insectes",
    "Grande sauterelle verte": "Insectes",
    "Grillon des bois": "Insectes",
    "Guêpes": "Insectes",
    "Gyrins": "Insectes",
    "Hanneton commun": "Insectes",
    "Ichneumons": "Insectes",
    "Longicornes": "Insectes",
    "Machaon": "Insectes",
    "Machilis": "Insectes",
    "Mante religieuse": "Insectes",
    "Méloés": "Insectes",
    "Miridés": "Insectes",
    "Moro-sphinx": "Insectes",
    "Mouche de la Saint-Marc": "Insectes",
    "Mouche de mai": "Insectes",
    "Mouches à damier": "Insectes",
    "Mouches stercoraires": "Insectes",
    "Mouches vertes": "Insectes",
    "Moustiques": "Insectes",
    "Nécrophores": "Insectes",
    "Nèpe cendrée": "Insectes",
    "Nepticule dorée": "Insectes",
    "Noctuelles": "Insectes",
    "Notonectes": "Insectes",
    "Œdémères": "Insectes",
    "Osmies": "Insectes",
    "Panorpes": "Insectes",
    "Paon-du-jour": "Insectes",
    "Perce-oreille commun": "Insectes",
    "Perles": "Insectes",
    "Petite biche": "Insectes",
    "Petite tortue": "Insectes",
    "Philène spumeuse": "Insectes",
    "Phryganes": "Insectes",
    "Piérides": "Insectes",
    "Poisson d'argent": "Insectes",
    "Psyché lustrée": "Insectes",
    "Pucerons": "Insectes",
    "Punaise arlequin": "Insectes",
    "Punaise nébuleuse": "Insectes",
    "Raphidies": "Insectes",
    "Scolytes": "Insectes",
    "Sialis de la vase": "Insectes",
    "Staphylins": "Insectes",
    "Sylvaine": "Insectes",
    "Sympétrums": "Insectes",
    "Syrphes": "Insectes",
    "Tachinaires": "Insectes",
    "Taons": "Insectes",
    "Taupins": "Insectes",
    "Tenthrèdes": "Insectes",
    "Thrips": "Insectes",
    "Tipules": "Insectes",
    "Tircis": "Insectes",
    "Trichies": "Insectes",
    "Yponomeutes": "Insectes",
    "Zygènes": "Insectes",
    "Coléoptères": "Insectes",
    "Diptères": "Insectes",
    "Éphéméroptères": "Insectes",
    "Hémiptères": "Insectes",
    "Hyménoptères": "Insectes",
    "Lépidoptères": "Insectes",
    "Zygoptères et Anisoptères": "Insectes",

    # Araignées
    "Agroecas": "Araignées",
    "Amaurobes": "Araignées",
    "Argiope fasciée": "Araignées",
    "Épeire diadème": "Araignées",
    "Linyphie triangulaire": "Araignées",
    "Lycoses": "Araignées",
    "Méta d'automne": "Araignées",
    "Misumène variable": "Araignées",
    "Pholque phalangiste": "Araignées",
    "Pisaure admirable": "Araignées",
    "Saltiques": "Araignées",
    "Ségestries": "Araignées",
    "Tégénaires": "Araignées",
    "Tétragnathes": "Araignées",
    "Xystiques": "Araignées",

    # Annélides, mollusques et arthropodes, hors araignées et insectes
    "Acariens": "Annélides, mollusques et arthropodes, hors araignées et insectes",
    "Ancyle": "Annélides, mollusques et arthropodes, hors araignées et insectes",
    "Anodonte des rivières": "Annélides, mollusques et arthropodes, hors araignées et insectes",
    "Aselles": "Annélides, mollusques et arthropodes, hors araignées et insectes",
    "Bouton commun": "Annélides, mollusques et arthropodes, hors araignées et insectes",
    "Cloportes": "Annélides, mollusques et arthropodes, hors araignées et insectes",
    "Écrevisse signal": "Annélides, mollusques et arthropodes, hors araignées et insectes",
    "Enchytréides": "Annélides, mollusques et arthropodes, hors araignées et insectes",
    "Erpobdelles (sangsues)": "Annélides, mollusques et arthropodes, hors araignées et insectes",
    "Gammares": "Annélides, mollusques et arthropodes, hors araignées et insectes",
    "Géophiles": "Annélides, mollusques et arthropodes, hors araignées et insectes",
    "Gloméris": "Annélides, mollusques et arthropodes, hors araignées et insectes",
    "Grande limnée": "Annélides, mollusques et arthropodes, hors araignées et insectes",
    "Iules": "Annélides, mollusques et arthropodes, hors araignées et insectes",
    "Limace léopard": "Annélides, mollusques et arthropodes, hors araignées et insectes",
    "Lithobies": "Annélides, mollusques et arthropodes, hors araignées et insectes",
    "Lombrics": "Annélides, mollusques et arthropodes, hors araignées et insectes",
    "Opilions": "Annélides, mollusques et arthropodes, hors araignées et insectes",
    "Orcheselles": "Annélides, mollusques et arthropodes, hors araignées et insectes",
    "Planorbes": "Annélides, mollusques et arthropodes, hors araignées et insectes",
    "Polydesmes": "Annélides, mollusques et arthropodes, hors araignées et insectes",
    "Pseudoscorpions": "Annélides, mollusques et arthropodes, hors araignées et insectes",
    "Scolopendres": "Annélides, mollusques et arthropodes, hors araignées et insectes",
    "Symphypléones": "Annélides, mollusques et arthropodes, hors araignées et insectes",
    "Ver de vase": "Annélides, mollusques et arthropodes, hors araignées et insectes",

    # Mammifères
    "Blaireau d'Europe": "Mammifères",
    "Campagnols": "Mammifères",
    "Castor d'Europe": "Mammifères",
    "Cerf élaphe": "Mammifères",
    "Chauves-souris": "Mammifères",
    "Chevreuil européen": "Mammifères",
    "Écureuil roux": "Mammifères",
    "Être humain": "Mammifères",
    "Fouine": "Mammifères",
    "Hérisson commun": "Mammifères",
    "Lapin de garenne": "Mammifères",
    "Lièvre d'Europe": "Mammifères",
    "Mulots": "Mammifères",
    "Musaraignes": "Mammifères",
    "Muscardin": "Mammifères",
    "Phoques": "Mammifères",
    "Ragondin": "Mammifères",
    "Rat musqué": "Mammifères",
    "Rat noir": "Mammifères",
    "Raton laveur": "Mammifères",
    "Renard roux": "Mammifères",
    "Sanglier": "Mammifères",
    "Surmulot": "Mammifères",
    "Taupe": "Mammifères",
    "Blaireau européen": "Mammifères",
    "Martre": "Mammifères",

    # Amphibiens et reptiles
    "Couleuvre helvétique": "Amphibiens et reptiles",
    "Crapaud commun": "Amphibiens et reptiles",
    "Grenouille rousse": "Amphibiens et reptiles",
    "Grenouilles vertes": "Amphibiens et reptiles",
    "Lézards": "Amphibiens et reptiles",
    "Orvet fragile": "Amphibiens et reptiles",
    "Salamandre tachetée": "Amphibiens et reptiles",
    "Triton alpestre": "Amphibiens et reptiles",
    "Triton palmé": "Amphibiens et reptiles",
    "Triton ponctué": "Amphibiens et reptiles",
    "Vipère péliade": "Amphibiens et reptiles",

    # Poissons
    "Anguille euro péenne": "Poissons",
    "Barbeau commun": "Poissons",
    "Brème commune": "Poissons",
    "Brochet": "Poissons",
    "Chabot commun": "Poissons",
    "Chevaine commun": "Poissons",
    "Flet d'Europe": "Poissons",
    "Ombre commun": "Poissons",
    "Petite roussette": "Poissons",
    "Raie bouclée": "Poissons",
    "Saumon atlantique": "Poissons",
    "Truite fario": "Poissons",

    # Mousses, hépatiques, sphaignes, fougères et prêles
    "Fougère aigle": "Mousses, hépatiques, sphaignes, fougères et prêles",
    "Hépatiques à feuilles": "Mousses, hépatiques, sphaignes, fougères et prêles",
    "Hépatiques à thalle": "Mousses, hépatiques, sphaignes, fougères et prêles",
    "Langue de cerf": "Mousses, hépatiques, sphaignes, fougères et prêles",
    "Mousses acrocarpes": "Mousses, hépatiques, sphaignes, fougères et prêles",
    "Mousses pleurocarpes": "Mousses, hépatiques, sphaignes, fougères et prêles",
    "Prêle des champs": "Mousses, hépatiques, sphaignes, fougères et prêles",
    "Rue des murailles": "Mousses, hépatiques, sphaignes, fougères et prêles",
    "Sphaignes": "Mousses, hépatiques, sphaignes, fougères et prêles",
    "Fausse-capillaire": "Mousses, hépatiques, sphaignes, fougères et prêles",
    "Fougère mâle": "Mousses, hépatiques, sphaignes, fougères et prêles",
    "Polypode vulgaire": "Mousses, hépatiques, sphaignes, fougères et prêles",
    "Polystic à aiguillons": "Mousses, hépatiques, sphaignes, fougères et prêles",
    "Scolopendre": "Mousses, hépatiques, sphaignes, fougères et prêles",

    # Champignons
    "Agarics": "Champignons",
    "Amanites": "Champignons",
    "Armillaires": "Champignons",
    "Bolets": "Champignons",
    "Calocère visqueuse": "Champignons",
    "Clitocybes": "Champignons",
    "Coprins": "Champignons",
    "Cortinaires": "Champignons",
    "Girolle": "Champignons",
    "Hypholome en touffes": "Champignons",
    "Inocybes": "Champignons",
    "Laccaire améthyste": "Champignons",
    "Lactaires": "Champignons",
    "Lépiotes": "Champignons",
    "Lycoperdon perlé": "Champignons",
    "Morilles": "Champignons",
    "Mycènes": "Champignons",
    "Paxilles": "Champignons",
    "Pezizes": "Champignons",
    "Pholiote changeante": "Champignons",
    "Pied bleu": "Champignons",
    "Pied-de-mouton": "Champignons",
    "Pleurotes": "Champignons",
    "Plutées": "Champignons",
    "Polypores": "Champignons",
    "Russules": "Champignons",
    "Satyre puant": "Champignons",
    "Sclérodermes": "Champignons",
    "Stérée hirsute": "Champignons",
    "Strophaire vert-de-gris": "Champignons",
    "Trémelle mésentérique": "Champignons",
    "Tricholomes": "Champignons",
    "Trompette de la mort": "Champignons",
    "Truffe de Bourgogne": "Champignons",
    "Volvaires": "Champignons",
    "Xylaire du bois": "Champignons",

    # Lichens
    "Type morphologique crustacé et lépreux": "Lichens",
    "Type morphologique foliacé": "Lichens",
    "Type morphologique fruticuleux": "Lichens",
    "Type morphologique complexe (ou composé)": "Lichens",
}


DATASETS = ["nature", "rando"]


class Command(BaseCommand):
    help = "Import taxons from CSV file"
    inaturalist_last_call = None
    xenocanto_last_call = None

    def add_arguments(self, parser):
        pass

    def extract_pdf_to_csv(self, pdf_path, csv_path):
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
        with pdfplumber.open(pdf_path) as pdf:
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

        with open(csv_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerows(hdrs)

    def validate_inaturalist(self, row):
        genre = row.get("Genre") or ""
        espece = row.get("Espèce") or ""
        famille = row.get("Famille") or ""
        ordre = (row.get("Ordre (Sous-ordre)") or "").split("(")[0].strip()
        classe = row.get("Classe") or ""
        embranchement = (row.get("Embranchement (Sous-embranchement)") or "").split("(")[0].strip()
        regne = row.get("Règne") or ""

        if espece and "spp." not in espece and "ssp." not in espece:
            scientific_name = f"{genre} {espece}"
        elif genre:
            scientific_name = genre
        elif famille:
            scientific_name = famille
        elif ordre:
            scientific_name = ordre
        elif classe:
            scientific_name = classe
        elif embranchement:
            scientific_name = embranchement
        elif regne:
            scientific_name = regne
        else:
            raise CommandError(f"Cannot determine scientific name for: {row.get('Nom vernaculaire')}")

        if self.inaturalist_last_call and (datetime.now() - self.inaturalist_last_call).total_seconds() < 1:
            time.sleep(2)  # Respect iNaturalist rate limit of 1 request per second
        self.inaturalist_last_call = datetime.now()
        try:
            resp = requests.get(
                "https://api.inaturalist.org/v1/taxa/autocomplete",
                params={"q": scientific_name, "per_page": 1},
                timeout=10,
            ).json()
        except Exception as e:
            raise CommandError(f"iNaturalist request failed for {scientific_name}: {e}")

        if not resp.get("results"):
            self.stdout.write(f"Not found in iNaturalist: {scientific_name} ({row.get('Nom vernaculaire')})")
            # raise CommandError(f"Not found in iNaturalist: {scientific_name} ({row.get('Nom vernaculaire')})")

    def validate_xenocanto(self, row):
        genre = row.get("Genre") or ""
        espece = row.get("Espèce") or ""

        if espece and espece != "spp.":
            species_query = f"gen:{genre} sp:{espece}"
        elif genre:
            species_query = f"gen:{genre}"
        else:
            raise CommandError(f"Cannot build Xeno-canto query for: {row.get('Nom vernaculaire')}")

        queries = [
            f"{species_query} cnt:Belgium type:song",
            f"{species_query} cnt:Belgium",
            f"{species_query} cnt:France type:song",
            f"{species_query} cnt:France",
        ]

        resp = None
        for query in queries:
            if self.xenocanto_last_call and (datetime.now() - self.xenocanto_last_call).total_seconds() < 1:
                time.sleep(2)  # Respect Xeno-canto rate limit of 1 request per second
            self.xenocanto_last_call = datetime.now()
            try:
                resp = requests.get(
                    "https://xeno-canto.org/api/3/recordings",
                    params={"query": query, "key": settings.XENOCANTO_API_KEY},
                    timeout=15,
                ).json()
            except Exception as e:
                raise CommandError(f"Xeno-canto request failed for {query}: {e}")
            if resp.get("recordings"):
                break

        if not resp or not resp.get("recordings"):
            self.stdout.write(f"Not found in Xeno-canto: {species_query} (tried Belgium/France, song/any) ({row.get('Nom vernaculaire')})")
            # raise CommandError(f"Not found in Xeno-canto: {species_query} ({row.get('Nom vernaculaire')})")

    def import_csv(self, csv_path, dataset_name):
        with open(csv_path, "r", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            created_count = 0
            updated_count = 0

            for row in reader:
                self.validate_inaturalist(row)
                if row.get("Classe") == "Aves":
                    self.validate_xenocanto(row)

                embranchement = row["Embranchement (Sous-embranchement)"] or ""
                if "(" in embranchement:
                    embranchement = embranchement.split("(")[0].strip()

                ordre = row["Ordre (Sous-ordre)"] or ""
                if "(" in ordre:
                    ordre = ordre.split("(")[0].strip()

                nom_vernaculaire = row["Nom vernaculaire"]
                if nom_vernaculaire not in CATEGORY_MAP:
                    self.stdout.write(
                        self.style.WARNING(
                            f"No category mapping for: '{nom_vernaculaire}' — importing with empty category"
                        )
                    )
                category = CATEGORY_MAP.get(nom_vernaculaire, "")

                taxon, created = Taxon.objects.update_or_create(
                    nom_vernaculaire=nom_vernaculaire,
                    dataset=dataset_name,
                    defaults={
                        "regne": row["Règne"],
                        "embranchement": embranchement,
                        "classe": row["Classe"],
                        "ordre": ordre,
                        "famille": row["Famille"],
                        "genre": row["Genre"],
                        "espece": row["Espèce"],
                        "partie_etat_indice": row["Partie/état/indice à reconnaitre"],
                        "category": category,
                    },
                )

                if created:
                    created_count += 1
                else:
                    updated_count += 1

        return created_count, updated_count

    def handle(self, *args, **options):
        total_created = 0
        total_updated = 0

        for dataset_name in DATASETS:
            csv_path = f"{dataset_name}.csv"
            pdf_path = f"{dataset_name}.pdf"

            if os.path.exists(csv_path):
                pass
            elif os.path.exists(pdf_path):
                self.stdout.write(f"Extracting {pdf_path} → {csv_path}...")
                self.extract_pdf_to_csv(pdf_path, csv_path)
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f"Neither {csv_path} nor {pdf_path} found — skipping dataset '{dataset_name}'"
                    )
                )
                continue

            self.stdout.write(f"Importing dataset '{dataset_name}' from {csv_path}...")
            created_count, updated_count = self.import_csv(csv_path, dataset_name)
            total_created += created_count
            total_updated += updated_count
            self.stdout.write(
                self.style.SUCCESS(
                    f"Dataset '{dataset_name}': Created={created_count}, Updated={updated_count}"
                )
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"\nImport complete! Total created: {total_created}, updated: {total_updated}"
            )
        )
