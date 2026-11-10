import unicodedata

ANIMAUX = [
    {"nom": "Lion", "habitat": "Savane", "regime": "Carnivore",
     "description": "Le roi de la savane vit en groupe appelé troupe."},
    {"nom": "Dauphin", "habitat": "Océan", "regime": "Carnivore",
     "description": "Mammifère marin très intelligent qui communique par sons."},
    {"nom": "Panda", "habitat": "Forêt de bambous", "regime": "Herbivore",
     "description": "Il mange jusqu'à 12 kg de bambou par jour."},
    {"nom": "Éléphant", "habitat": "Savane", "regime": "Herbivore",
     "description": "Le plus grand animal terrestre, avec une mémoire remarquable."},
    {"nom": "Pingouin", "habitat": "Régions polaires", "regime": "Carnivore",
     "description": "Oiseau qui ne vole pas mais nage très bien."},
    {"nom": "Girafe", "habitat": "Savane", "regime": "Herbivore",
     "description": "Le plus haut des animaux terrestres : jusqu'à 5 mètres."},
    {"nom": "Tigre", "habitat": "Forêt tropicale", "regime": "Carnivore",
     "description": "Le plus grand des félins, reconnaissable à ses rayures uniques."},
    {"nom": "Loup", "habitat": "Forêt", "regime": "Carnivore",
     "description": "Il chasse en meute et communique en hurlant."},
    {"nom": "Ours polaire", "habitat": "Banquise", "regime": "Carnivore",
     "description": "Sa fourrure paraît blanche, mais sa peau est noire."},
    {"nom": "Requin", "habitat": "Océan", "regime": "Carnivore",
     "description": "Il existe depuis plus de 400 millions d'années."},
    {"nom": "Aigle", "habitat": "Montagne", "regime": "Carnivore",
     "description": "Sa vue perçante repère une proie à plusieurs kilomètres."},
    {"nom": "Kangourou", "habitat": "Plaines d'Australie", "regime": "Herbivore",
     "description": "Il se déplace en sautant et porte son petit dans une poche."},
    {"nom": "Koala", "habitat": "Forêt d'eucalyptus", "regime": "Herbivore",
     "description": "Il dort jusqu'à 20 heures par jour."},
    {"nom": "Crocodile", "habitat": "Fleuves et marécages", "regime": "Carnivore",
     "description": "Un reptile redoutable qui existe depuis l'époque des dinosaures."},
    {"nom": "Tortue", "habitat": "Îles et océans", "regime": "Omnivore",
     "description": "Elle garde sa carapace toute sa vie et peut vivre plus de 100 ans."},
]


def normaliser(texte):
    # "Éléphant " devient "elephant" : minuscules, sans accents, sans espaces autour
    texte = unicodedata.normalize("NFD", texte)
    texte = "".join(c for c in texte if unicodedata.category(c) != "Mn")
    return texte.strip().lower()


def trouver_animal(nom):
    for animal in ANIMAUX:
        if normaliser(animal["nom"]) == normaliser(nom):
            return animal
    return None