import unicodedata

ANIMAUX = [
    {
        "nom": "Lion",
        "habitat": "Savane",
        "regime": "Carnivore",
        "description": "Le roi de la savane vit en groupe appelé troupe.",
    },
    {
        "nom": "Dauphin",
        "habitat": "Océan",
        "regime": "Carnivore",
        "description": "Mammifère marin très intelligent qui communique par sons.",
    },
    {
        "nom": "Panda",
        "habitat": "Forêt de bambous",
        "regime": "Herbivore",
        "description": "Il mange jusqu'à 12 kg de bambou par jour.",
    },
    {
        "nom": "Éléphant",
        "habitat": "Savane",
        "regime": "Herbivore",
        "description": "Le plus grand animal terrestre, avec une mémoire remarquable.",
    },
    {
        "nom": "Pingouin",
        "habitat": "Régions polaires",
        "regime": "Carnivore",
        "description": "Oiseau qui ne vole pas mais nage très bien.",
    },
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

