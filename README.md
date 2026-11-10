# QuizAnimaux, bot Discord

Bot Discord sur le thème des animaux : encyclopédie, adoption, inventaire et quiz avec classement.

## Installation

1. Installer les dépendances :
   pip install -r requirements.txt
2. Créer un fichier `.env` à la racine (voir `.env.example`) :
   DISCORD_TOKEN=ton_token
   SALON_JEU_ID=identifiant_du_salon_du_jeu
3. Activer "Message Content Intent" et "Server Members Intent" dans le portail
   développeur Discord, puis inviter le bot sur un serveur.
4. Lancer le bot :
   python main.py

## Commandes

Les commandes du jeu fonctionnent uniquement dans le salon défini par `SALON_JEU_ID`.

| Commande | Description |
|---|---|
| `!regles` / `!aide` | Affiche la carte des règles (fonctionne partout) |
| `!animaux` | Liste les animaux disponibles |
| `!animal <nom>` | Affiche la fiche d'un animal (embed) |
| `!adopter <nom>` | Adopte un animal |
| `!collection` | Affiche tes animaux adoptés |
| `!inventaire` | Montre les animaux collectionnés et ceux qu'il reste à trouver |
| `!quiz` | Pose une question (40 secondes pour répondre) |
| `!score` | Affiche tes points |
| `!classement` | Affiche le top 5 des joueurs |
| `!ping` | Commande de test (fonctionne partout) |

## Règles du quiz

- Bonne réponse : +1 point
- Mauvaise réponse : -1 point (le score ne descend jamais sous 0)
- Temps écoulé : 0 point

Quand un nouveau membre rejoint le serveur, la carte des règles est envoyée dans #général.

## Sauvegarde

Les données sont enregistrées en JSON (`donnees.json` pour les collections,
`scores.json` pour les points) et rechargées au redémarrage du bot.

## Structure

- `main.py` : le bot et ses commandes
- `animaux.py` : données des animaux et recherche
- `questions.py` : questions du quiz
- `stockage.py` : lecture et écriture des fichiers JSON