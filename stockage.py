import json

FICHIER = "donnees.json"
FICHIER_SCORES = "scores.json"


def charger(fichier=FICHIER):
    try:
        with open(fichier, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def sauvegarder(donnees, fichier=FICHIER):
    with open(fichier, "w", encoding="utf-8") as f:
        json.dump(donnees, f, ensure_ascii=False, indent=4)