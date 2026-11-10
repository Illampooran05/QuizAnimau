import asyncio
import os
import random

import discord
from discord.ext import commands
from dotenv import load_dotenv

from animaux import ANIMAUX, trouver_animal, normaliser
from questions import QUESTIONS
from image import IMAGES
from stockage import charger, sauvegarder, FICHIER_SCORES

load_dotenv()

# salon où se joue le jeu (modifiable dans le .env, sinon ton salon par défaut)
SALON_JEU_ID = int(os.getenv("SALON_JEU_ID", "1568258353833050152"))
# salon d'annonces (facultatif) : si vide, le bot écrit dans le salon où tu tapes la commande
ID_SALON_ANNONCES = int(os.getenv("SALON_ANNONCES_ID", "0"))
# commandes utilisables dans n'importe quel salon
COMMANDES_LIBRES = {"regles", "ping", "publier_regles", "annonce", "publier_quiz"}
TEMPS_QUIZ = 40        # secondes pour répondre au quiz
TEMPS_BOUTON = 60      # secondes pendant lesquelles le bouton "suivante" reste actif

intents = discord.Intents.default()
intents.message_content = True
intents.members = True          # nécessaire pour on_member_join
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

donnees = charger()
scores = charger(FICHIER_SCORES)
quiz_en_cours = set()           # joueurs qui ont déjà une question en cours


def creer_embed_regles():
    embed = discord.Embed(
        title="📜 Règles du jeu",
        description=(
            f"Découvre {len(ANIMAUX)} animaux, adopte-les et gagne des points au quiz !\n"
            f"🎮 Le jeu se passe dans <#{SALON_JEU_ID}>."
        ),
        color=discord.Color.gold(),
    )
    embed.add_field(
        name="🎯 Le but",
        value="Avoir le plus de points possible et finir premier du `!classement`.",
        inline=False,
    )
    embed.add_field(
        name="❓ Le quiz",
        value=(
            "• Lance `!quiz` : une question sur les animaux est tirée au hasard\n"
            f"• Tu as **{TEMPS_QUIZ} secondes** pour répondre dans le salon\n"
            "• Écris seulement la réponse, sans phrase (exemple : `lion`)\n"
            "• Les majuscules et les accents ne comptent pas\n"
            "• Après chaque question, clique sur **▶️ Question suivante** pour enchaîner"
        ),
        inline=False,
    )
    embed.add_field(
        name="🏆 Les points",
        value=(
            "• Bonne réponse : **+1 point**\n"
            "• Mauvaise réponse : **-1 point** (ton score ne descend jamais sous 0)\n"
            "• Temps écoulé : **0 point**\n"
            "• Tes points sont sauvegardés, même si le bot redémarre"
        ),
        inline=False,
    )
    embed.add_field(
        name="📊 Score et classement",
        value=(
            "• `!score` affiche tes points\n"
            "• `!classement` affiche le top 5 des joueurs"
        ),
        inline=False,
    )
    embed.add_field(
        name="🐾 L'adoption",
        value=(
            "• `!animaux` pour voir la liste, `!animal <nom>` pour la fiche\n"
            "• `!adopter <nom>` pour ajouter un animal à ta collection\n"
            "• `!inventaire` pour voir ce que tu as déjà collectionné\n"
            "• Chaque animal ne peut être adopté qu'une fois"
        ),
        inline=False,
    )
    embed.add_field(
        name="🚀 À vous de jouer !",
        value="Tape `!quiz` dans le salon du jeu pour commencer.",
        inline=False,
    )
    return embed


def creer_embed_quiz():
    embed = discord.Embed(
        title="❓ Comment jouer au quiz",
        description="Teste tes connaissances sur les animaux et monte dans le classement !",
        color=discord.Color.purple(),
    )
    embed.add_field(
        name="1️⃣ Lancer une question",
        value="Tape `!quiz` dans le salon du jeu.",
        inline=False,
    )
    embed.add_field(
        name="2️⃣ Répondre",
        value=(
            f"Tu as **{TEMPS_QUIZ} secondes**. Écris juste la réponse, "
            "par exemple `lion` ou `panda`."
        ),
        inline=False,
    )
    embed.add_field(
        name="3️⃣ Gagner des points",
        value="**+1** si c'est bon, **-1** si c'est faux, **0** si le temps est écoulé.",
        inline=False,
    )
    embed.add_field(
        name="4️⃣ Enchaîner",
        value="Clique sur **▶️ Question suivante** sous le résultat, sans retaper `!quiz`.",
        inline=False,
    )
    return embed


async def publier_embed(salon, embed, reactions=("✅",), message=None):
    # envoie une carte puis ajoute les réactions demandées dessous
    envoye = await salon.send(content=message, embed=embed)
    for emoji in reactions:
        try:
            await envoye.add_reaction(emoji)
        except discord.Forbidden:
            break       # le bot n'a pas la permission d'ajouter des réactions
    return envoye


async def envoyer_regles(salon, message=None):
    return await publier_embed(salon, creer_embed_regles(), ("✅",), message)


def trouver_salon_general(guild):
    # accepte "général" et "general"
    for salon in guild.text_channels:
        if normaliser(salon.name) == "general":
            return salon
    return guild.system_channel     # plan B : le salon d'accueil du serveur


def trouver_salon_annonces(ctx):
    salon = bot.get_channel(ID_SALON_ANNONCES)      # None si l'identifiant est 0
    return salon or ctx.channel


def modifier_points(auteur, delta):
    profil = scores.setdefault(
        str(auteur.id), {"nom": auteur.display_name, "points": 0}
    )
    profil["nom"] = auteur.display_name
    profil["points"] = max(0, profil["points"] + delta)    # jamais sous 0
    sauvegarder(scores, FICHIER_SCORES)
    return profil["points"]


class BoutonSuivant(discord.ui.View):
    # bouton affiché sous le résultat d'un quiz pour passer à la question suivante
    def __init__(self, joueur):
        super().__init__(timeout=TEMPS_BOUTON)
        self.joueur = joueur
        self.message = None

    @discord.ui.button(label="Question suivante", emoji="▶️", style=discord.ButtonStyle.success)
    async def suivante(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.joueur:
            await interaction.response.send_message(
                "Ce bouton est réservé au joueur qui vient de répondre. Tape `!quiz` pour jouer !",
                ephemeral=True,
            )
            return

        self.stop()
        button.disabled = True      # le bouton ne sert qu'une fois
        await interaction.response.edit_message(view=self)
        await jouer_quiz(interaction.channel, self.joueur)

    async def on_timeout(self):
        # après TEMPS_BOUTON secondes, on grise le bouton
        for bouton in self.children:
            bouton.disabled = True
        if self.message is not None:
            try:
                await self.message.edit(view=self)
            except discord.HTTPException:
                pass


async def jouer_quiz(salon, joueur):
    # pose une question, attend la réponse, donne le résultat et propose la suivante
    if joueur.id in quiz_en_cours:
        await salon.send(f"{joueur.mention}, tu as déjà une question en cours !")
        return
    quiz_en_cours.add(joueur.id)

    q = random.choice(QUESTIONS)
    await salon.send(f"❓ {q['question']} (tu as {TEMPS_QUIZ} secondes)")

    def check(message):
        return message.author == joueur and message.channel == salon

    try:
        message = await bot.wait_for("message", check=check, timeout=TEMPS_QUIZ)
    except asyncio.TimeoutError:
        texte = f"⏰ Temps écoulé ! La réponse était {q['reponses'][0]}."
    else:
        if normaliser(message.content) in q["reponses"]:
            total = modifier_points(joueur, 1)
            texte = f"✅ Bonne réponse ! +1 point. Tu as {total} point(s)."
        else:
            total = modifier_points(joueur, -1)
            texte = f"❌ Raté, c'était {q['reponses'][0]}. -1 point. Tu as {total} point(s)."
    finally:
        quiz_en_cours.discard(joueur.id)

    vue = BoutonSuivant(joueur)
    vue.message = await salon.send(texte, view=vue)


@bot.check
async def salon_autorise(ctx):
    # les commandes du jeu ne marchent que dans le salon du jeu
    if ctx.command.name in COMMANDES_LIBRES:
        return True
    return ctx.channel.id == SALON_JEU_ID


@bot.event
async def on_command_error(ctx, erreur):
    # MissingPermissions doit être testée avant CheckFailure (c'est une sous-classe)
    if isinstance(erreur, commands.MissingPermissions):
        await ctx.send("🔒 Cette commande est réservée aux administrateurs.")
    elif isinstance(erreur, commands.CheckFailure):
        await ctx.send(f"🎮 Les commandes du jeu se jouent dans <#{SALON_JEU_ID}>.")
    elif isinstance(erreur, commands.CommandNotFound):
        pass
    else:
        raise erreur


@bot.event
async def on_ready():
    print(f"Connecte en tant que {bot.user}")


@bot.event
async def on_member_join(member):
    salon = trouver_salon_general(member.guild)
    if salon is not None:
        await envoyer_regles(salon, f"👋 Bienvenue {member.mention} !")


# Commande prefixee : !ping
@bot.command()
async def ping(ctx):
    await ctx.send("Pong !")


@bot.command(name="regles", aliases=["règles", "regle", "aide", "help"])
async def regles(ctx):
    await ctx.send(embed=creer_embed_regles())


@bot.command(name="publier_regles")
@commands.has_permissions(administrator=True)
async def publier_regles(ctx):
    # à taper dans le salon où les règles doivent rester affichées
    await envoyer_regles(ctx.channel)
    try:
        await ctx.message.delete()      # supprime ta commande
    except discord.Forbidden:
        pass


@bot.command(name="publier_quiz")
@commands.has_permissions(administrator=True)
async def publier_quiz(ctx):
    await publier_embed(trouver_salon_annonces(ctx), creer_embed_quiz(), ("🎯",))


@bot.command(name="annonce")
@commands.has_permissions(administrator=True)
async def annonce(ctx, *, texte=None):
    if texte is None:
        await ctx.send("Utilise la commande comme ça : `!annonce ton message`")
        return

    embed = discord.Embed(
        title="📢 Annonce",
        description=texte,
        color=discord.Color.orange(),
    )
    embed.set_footer(text=f"Par {ctx.author.display_name}")
    await publier_embed(trouver_salon_annonces(ctx), embed, ("✅", "👍"))

    try:
        await ctx.message.delete()      # supprime ta commande pour garder le salon propre
    except discord.Forbidden:
        pass


@bot.command()
async def animaux(ctx):
    noms = [a["nom"] for a in ANIMAUX]
    await ctx.send("🐾 Animaux disponibles : " + ", ".join(noms))


@bot.command()
async def animal(ctx, *, nom=None):
    if nom is None:
        await ctx.send("Utilise la commande comme ça : `!animal lion`")
        return

    trouve = trouver_animal(nom)
    if trouve is None:
        await ctx.send(f"Je ne connais pas « {nom} ». Tape `!animaux` pour voir la liste.")
        return

    embed = discord.Embed(
        title=f"🐾 {trouve['nom']}",
        description=trouve["description"],
        color=discord.Color.green(),
    )
    embed.add_field(name="Habitat", value=trouve["habitat"], inline=True)
    embed.add_field(name="Régime", value=trouve["regime"], inline=True)

    image = IMAGES.get(trouve["nom"])
    if image:
        embed.set_image(url=image)

    await ctx.send(embed=embed)


@bot.command()
async def adopter(ctx, *, nom=None):
    if nom is None:
        await ctx.send("Utilise la commande comme ça : `!adopter panda`")
        return

    trouve = trouver_animal(nom)
    if trouve is None:
        await ctx.send(f"Je ne connais pas « {nom} ». Tape `!animaux` pour voir la liste.")
        return

    mes_animaux = donnees.setdefault(str(ctx.author.id), [])
    if trouve["nom"] in mes_animaux:
        await ctx.send(f"Tu as déjà adopté {trouve['nom']} !")
        return

    mes_animaux.append(trouve["nom"])
    sauvegarder(donnees)
    await ctx.send(f"🎉 {ctx.author.mention} a adopté {trouve['nom']} !")


@bot.command()
async def collection(ctx):
    mes_animaux = donnees.get(str(ctx.author.id), [])
    if not mes_animaux:
        await ctx.send("Tu n'as encore adopté aucun animal. Essaie `!adopter lion`.")
        return
    await ctx.send("🏡 Ta collection : " + ", ".join(mes_animaux))


@bot.command(name="inventaire", aliases=["inventory", "inv"])
async def inventaire(ctx):
    mes_animaux = donnees.get(str(ctx.author.id), [])

    lignes = []
    possedes = 0
    for a in ANIMAUX:
        if a["nom"] in mes_animaux:
            lignes.append(f"✅ **{a['nom']}** · {a['habitat']}")
            possedes += 1
        else:
            lignes.append(f"🔒 {a['nom']}")

    embed = discord.Embed(
        title=f"🎒 Inventaire de {ctx.author.display_name}",
        description="\n".join(lignes),
        color=discord.Color.blue(),
    )
    embed.set_footer(text=f"{possedes}/{len(ANIMAUX)} animaux collectionnés")
    await ctx.send(embed=embed)


@bot.command()
async def quiz(ctx):
    await jouer_quiz(ctx.channel, ctx.author)


@bot.command()
async def score(ctx):
    profil = scores.get(str(ctx.author.id))
    points = profil["points"] if profil else 0
    await ctx.send(f"🏆 {ctx.author.mention}, tu as {points} point(s).")


@bot.command()
async def classement(ctx):
    if not scores:
        await ctx.send("Personne n'a encore de points. Lance `!quiz` !")
        return

    tri = sorted(scores.values(), key=lambda p: p["points"], reverse=True)
    lignes = [
        f"{i}. {p['nom']} : {p['points']} point(s)"
        for i, p in enumerate(tri[:5], start=1)
    ]
    await ctx.send("🏅 Classement :\n" + "\n".join(lignes))


bot.run(os.getenv("DISCORD_TOKEN"))