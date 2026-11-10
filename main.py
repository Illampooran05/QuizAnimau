import asyncio
import os
import random

import discord
from discord.ext import commands
from dotenv import load_dotenv

from animaux import ANIMAUX, trouver_animal, normaliser
from questions import QUESTIONS
from stockage import charger, sauvegarder, FICHIER_SCORES

load_dotenv()

# salon où se joue le jeu (modifiable dans le .env, sinon ton salon par défaut)
SALON_JEU_ID = int(os.getenv("SALON_JEU_ID", "1568258353833050152"))
COMMANDES_LIBRES = {"regles", "ping"}    # utilisables dans n'importe quel salon

intents = discord.Intents.default()
intents.message_content = True
intents.members = True          # nécessaire pour on_member_join
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

donnees = charger()
scores = charger(FICHIER_SCORES)


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
            "• Lance `!quiz` : une question est posée\n"
            "• Tu as **20 secondes** pour répondre dans le salon\n"
            "• Les majuscules et les accents ne comptent pas\n"
            "• Seule **ta** réponse est prise en compte"
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
        name="🐾 L'adoption",
        value=(
            "• `!animaux` pour voir la liste, `!animal <nom>` pour la fiche\n"
            "• `!adopter <nom>` pour ajouter un animal à ta collection\n"
            "• `!inventaire` pour voir ce que tu as déjà collectionné\n"
            "• Chaque animal ne peut être adopté qu'une fois"
        ),
        inline=False,
    )
    embed.set_footer(text="Prêt ? Tape !quiz pour commencer")
    return embed


def trouver_salon_general(guild):
    # accepte "général" et "general"
    for salon in guild.text_channels:
        if normaliser(salon.name) == "general":
            return salon
    return guild.system_channel     # plan B : le salon d'accueil du serveur


def modifier_points(auteur, delta):
    profil = scores.setdefault(
        str(auteur.id), {"nom": auteur.display_name, "points": 0}
    )
    profil["nom"] = auteur.display_name
    profil["points"] = max(0, profil["points"] + delta)    # jamais sous 0
    sauvegarder(scores, FICHIER_SCORES)
    return profil["points"]


@bot.check
async def salon_autorise(ctx):
    # les commandes du jeu ne marchent que dans le salon du jeu
    if ctx.command.name in COMMANDES_LIBRES:
        return True
    return ctx.channel.id == SALON_JEU_ID


@bot.event
async def on_command_error(ctx, erreur):
    if isinstance(erreur, commands.CheckFailure):
        await ctx.send(f"🎮 Les commandes du jeu se jouent dans <#{SALON_JEU_ID}>.")
    elif isinstance(erreur, commands.CommandNotFound):
        pass
    else:
        raise erreur


@bot.event
async def on_ready():
    # Envoie les commandes slash a Discord au demarrage.
    await bot.tree.sync()
    print(f"Connecte en tant que {bot.user}")


@bot.event
async def on_member_join(member):
    salon = trouver_salon_general(member.guild)
    if salon is not None:
        await salon.send(f"👋 Bienvenue {member.mention} !", embed=creer_embed_regles())


# Commande prefixee : !ping
@bot.command()
async def ping(ctx):
    await ctx.send("Pong !")


# Commande slash : /salut
@bot.tree.command(name="salut", description="Le bot te dit bonjour")
async def salut(interaction: discord.Interaction):
    await interaction.response.send_message(f"Salut {interaction.user.mention} !")


@bot.command(name="regles", aliases=["règles", "regle", "aide", "help"])
async def regles(ctx):
    await ctx.send(embed=creer_embed_regles())


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
    q = random.choice(QUESTIONS)
    await ctx.send(f"❓ {q['question']} (tu as 40 secondes)")

    def check(message):
        return message.author == ctx.author and message.channel == ctx.channel

    try:
        message = await bot.wait_for("message", check=check, timeout=40)
    except asyncio.TimeoutError:
        await ctx.send(f"⏰ Temps écoulé ! La réponse était {q['reponses'][0]}.")
        return

    if normaliser(message.content) in q["reponses"]:
        total = modifier_points(ctx.author, 1)
        await ctx.send(f"✅ Bonne réponse ! +1 point. Tu as {total} point(s).")
    else:
        total = modifier_points(ctx.author, -1)
        await ctx.send(
            f"❌ Raté, c'était {q['reponses'][0]}. -1 point. Tu as {total} point(s)."
        )


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